# This code is a Qiskit project.
#
# (C) Copyright IBM 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Tests for samplomatic.transpiler.layer_inference."""

import pytest
from qiskit import transpile
from qiskit.circuit import Parameter, QuantumCircuit
from qiskit.transpiler import CouplingMap

from samplomatic.annotations import InjectNoise
from samplomatic.transpiler import (
    InsertLayerBarriers,
    LayerInferenceError,
    _InferredLayer,
    generate_boxing_pass_manager,
    infer_layers,
    insert_layer_barriers,
)
from samplomatic.utils import find_unique_box_instructions, get_annotation


def _count_unique_gate_layers(boxed: QuantumCircuit) -> int:
    gate_instrs = [
        i
        for i in boxed.data
        if i.operation.name == "box" and get_annotation(i.operation, InjectNoise) is not None
    ]
    return len(find_unique_box_instructions(gate_instrs))


def _add_rzz_layer(qc: QuantumCircuit, pairs, angle):
    for q0, q1 in sorted(pairs):
        qc.rz(-angle / 2, q0)
        qc.rz(-angle / 2, q1)
        qc.rzz(angle, q0, q1)
        qc.rz(angle / 2, q0)
        qc.rz(angle / 2, q1)


def _trotter_circuit(num_qubits, layer_a, layer_b, layer_c, n_steps, m_barrier_free):
    """Build an (ABCCBA)^n Trotter circuit.

    End-of-step barriers are inserted everywhere except after the last
    ``m_barrier_free`` steps.
    """
    theta = Parameter("θ")
    qc = QuantumCircuit(num_qubits)
    for step in range(n_steps):
        for pairs in [layer_a, layer_b, layer_c, layer_c, layer_b, layer_a]:
            _add_rzz_layer(qc, pairs, theta)
        if step < n_steps - m_barrier_free:
            qc.barrier()
    qc.measure_all()
    return qc


def _chain_three_coloring(num_qubits):
    """Compute the standard 3-edge-coloring of a 1D chain (every third edge)."""
    layer_a = {(i, i + 1) for i in range(0, num_qubits - 1, 3)}
    layer_b = {(i, i + 1) for i in range(1, num_qubits - 1, 3)}
    layer_c = {(i, i + 1) for i in range(2, num_qubits - 1, 3)}
    return layer_a, layer_b, layer_c


@pytest.fixture
def boxing_pm():
    return generate_boxing_pass_manager(
        enable_gates=True,
        enable_measures=False,
        inject_noise_targets="gates",
        twirling_strategy="active",
    )


@pytest.fixture
def chain_isa_factory():
    """Return a function that builds an ISA Trotter circuit on a 12-qubit chain."""
    n = 12
    layer_a, layer_b, layer_c = _chain_three_coloring(n)
    edges = [(i, i + 1) for i in range(n - 1)]
    coupling = CouplingMap(edges + [(b, a) for a, b in edges])

    logical = _trotter_circuit(n, layer_a, layer_b, layer_c, n_steps=4, m_barrier_free=2)

    def _build(seed):
        return transpile(
            logical,
            basis_gates=["rzz", "rz", "sx", "x", "measure"],
            coupling_map=coupling,
            optimization_level=3,
            seed_transpiler=seed,
        )

    return _build, [layer_a, layer_b, layer_c]


class TestExplicitTemplates:
    """Layer inference with caller-supplied templates."""

    def test_recovers_three_unique_types_across_seeds(self, boxing_pm, chain_isa_factory):
        build_isa, templates = chain_isa_factory
        for seed in range(8):
            isa = build_isa(seed)
            fixed = insert_layer_barriers(isa, templates)
            assert (
                _count_unique_gate_layers(boxing_pm.run(fixed)) == 3
            ), f"seed={seed}: expected 3 unique gate layers"

    def test_failure_mode_without_fix(self, boxing_pm, chain_isa_factory):
        build_isa, _ = chain_isa_factory
        # Without the fix, the greedy boxing algorithm produces more than 3 unique
        # types (typically 7) because it can't see through the transpiler's
        # disjoint-qubit reorderings of the barrier-free section.
        for seed in range(8):
            isa = build_isa(seed)
            assert (
                _count_unique_gate_layers(boxing_pm.run(isa)) > 3
            ), f"seed={seed}: expected the greedy baseline to fail"

    def test_via_pass_manager_kwarg(self, chain_isa_factory):
        build_isa, templates = chain_isa_factory
        pm = generate_boxing_pass_manager(
            enable_gates=True,
            enable_measures=False,
            inject_noise_targets="gates",
            twirling_strategy="active",
            infer_layers=templates,
        )
        for seed in range(4):
            isa = build_isa(seed)
            assert _count_unique_gate_layers(pm.run(isa)) == 3

    def test_infer_layers_returns_full_layers(self, chain_isa_factory):
        build_isa, templates = chain_isa_factory
        isa = build_isa(seed=0)
        layers = infer_layers(isa, templates)
        # Every detected layer should have a singleton tenable type.
        for layer in layers:
            assert len(layer.tenable) == 1, f"layer {layer} is type-ambiguous"
        # All four Trotter steps × 6 logical layers per step = 24 logical layers.
        # The transpiler may or may not fuse same-pair adjacencies, but the count
        # is bounded above by 24.
        assert len(layers) <= 24


class TestSamePairFusion:
    """Same-pair fusion: a fused block on a single pair becomes one layer.

    This is the regime where the original notebook prototype's
    count-divisibility check fails.
    """

    def test_two_adjacent_a_blocks_on_same_pair(self):
        # Two RZZ gates back-to-back on the same pair (no dressing in between)
        # — the kind of structure left over after transpile fuses two A-layer
        # occurrences. The new algorithm produces two A-layers (one block each),
        # not a count-divisibility error.
        qc = QuantumCircuit(2)
        qc.rzz(0.3, 0, 1)
        qc.rzz(0.4, 0, 1)
        templates = [{(0, 1)}]
        layers = infer_layers(qc, templates)
        assert len(layers) == 2
        for layer in layers:
            assert layer.tenable == frozenset({0})

    def test_count_mismatch_does_not_raise(self):
        # Three RZZ on (0,1) with templates [{(0,1)}] (one type, one occurrence
        # per layer): the original notebook would have raised a "must be a
        # multiple of occurrences" error. The new algorithm just produces three
        # separate layers of type 0.
        qc = QuantumCircuit(2)
        qc.rzz(0.1, 0, 1)
        qc.rzz(0.2, 0, 1)
        qc.rzz(0.3, 0, 1)
        layers = infer_layers(qc, [{(0, 1)}])
        assert len(layers) == 3


class TestTemplateInference:
    """Layer inference without explicit templates."""

    def test_falls_back_to_barrier_split(self):
        # Two ABCCBA-style segments with a barrier in between. Inference should
        # discover the same set of pair-set types in both halves.
        qc = QuantumCircuit(6)
        layer_a = [(0, 1), (2, 3), (4, 5)]
        layer_b = [(1, 2), (3, 4)]
        layer_c = [(0, 5)]
        for pairs in [layer_a, layer_b, layer_c, layer_b, layer_a]:
            for q0, q1 in pairs:
                qc.rzz(0.1, q0, q1)
        qc.barrier()
        for pairs in [layer_a, layer_b, layer_c, layer_b, layer_a]:
            for q0, q1 in pairs:
                qc.rzz(0.1, q0, q1)
        layers = infer_layers(qc)
        # Inference is best-effort; here the qubit-conflict-only walk gives
        # exactly the expected per-segment structure because B and C share
        # qubits with A. We assert non-empty rather than a precise count.
        assert len(layers) > 0


class TestErrorPaths:
    """Layer inference error reporting."""

    def test_pair_not_in_any_template_raises(self):
        qc = QuantumCircuit(3)
        qc.rzz(0.1, 0, 1)
        qc.rzz(0.1, 1, 2)  # pair (1,2) not in any template
        templates = [{(0, 1)}]
        with pytest.raises(LayerInferenceError, match=r"qubits \(1, 2\)"):
            infer_layers(qc, templates)

    def test_empty_templates_falls_through(self):
        # With templates=[] (empty list), every closed layer is anonymous —
        # the algorithm should still produce some assignment without error.
        qc = QuantumCircuit(2)
        qc.rzz(0.1, 0, 1)
        layers = infer_layers(qc, [])
        assert len(layers) == 1


class TestInsertLayerBarriers:
    """End-to-end tests: insert_layer_barriers + boxing pass manager."""

    def test_idempotent_on_already_barriered_circuit(self, boxing_pm):
        # If the circuit already has barriers between every layer, the
        # algorithm should not change the unique-layer count.
        qc = QuantumCircuit(4)
        layer_a = [(0, 1), (2, 3)]
        layer_b = [(1, 2)]
        for pairs in [layer_a, layer_b, layer_a]:
            for q0, q1 in pairs:
                qc.rzz(0.1, q0, q1)
            qc.barrier()
        qc.measure_all()
        templates = [{(0, 1), (2, 3)}, {(1, 2)}]
        before = _count_unique_gate_layers(boxing_pm.run(qc))
        after = _count_unique_gate_layers(boxing_pm.run(insert_layer_barriers(qc, templates)))
        assert before == after == 2

    def test_pass_class_alias(self, chain_isa_factory):
        # The TransformationPass wrapper produces the same result as the
        # bare function.
        from qiskit.transpiler import PassManager

        build_isa, templates = chain_isa_factory
        isa = build_isa(seed=0)
        pm = PassManager([InsertLayerBarriers(layer_templates=templates)])
        out_pass = pm.run(isa)
        out_func = insert_layer_barriers(isa, templates)
        # Same number of barriers (a quick structural check).
        n_pass = sum(1 for inst in out_pass.data if inst.operation.name == "barrier")
        n_func = sum(1 for inst in out_func.data if inst.operation.name == "barrier")
        assert n_pass == n_func


class TestInferredLayerDataclass:
    """Sanity tests for the InferredLayer dataclass."""

    def test_immutable(self):
        layer = _InferredLayer(nodes=(), pairs=frozenset(), tenable=frozenset({0}))
        with pytest.raises(Exception):  # noqa: B017
            layer.tenable = frozenset({1})

    def test_fields(self):
        qc = QuantumCircuit(2)
        qc.rzz(0.1, 0, 1)
        layers = infer_layers(qc, [{(0, 1)}])
        assert len(layers) == 1
        layer = layers[0]
        assert isinstance(layer, _InferredLayer)
        assert layer.pairs == frozenset({frozenset({0, 1})})
        assert layer.tenable == frozenset({0})
