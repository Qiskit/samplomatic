# This code is a Qiskit project.
#
# (C) Copyright IBM 2025.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Test PreSamplex"""

import numpy as np
import pytest
from qiskit.circuit import CircuitInstruction, ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.circuit.library import CXGate, Measure, XGate
from rustworkx import topological_sort

from samplomatic import Twirl
from samplomatic.annotations import VirtualType
from samplomatic.builders import pre_build
from samplomatic.builders.specs import InstructionMode, InstructionSpec
from samplomatic.constants import Direction
from samplomatic.exceptions import SamplexBuildError
from samplomatic.optionals import HAS_PLOTLY
from samplomatic.partition import QubitIndicesPartition, QubitPartition, SubsystemIndicesPartition
from samplomatic.pre_samplex import PreSamplex
from samplomatic.pre_samplex.graph_data import PreCollect, PreEmit, PrePropagate, PreZ2Collect
from samplomatic.pre_samplex.pre_samplex import DanglerMatch, DanglerType
from samplomatic.synths.rzsx_synth import RzSxSynth
from samplomatic.virtual_registers import PauliRegister


class TestDanglers:
    """Test danglers handling"""

    def test_add_then_find_danglers(self):
        """Test that added danglers are then found"""
        qreg = QuantumRegister(2)
        qubit_idxs = QubitIndicesPartition.from_elements([0, 1])
        pre_samplex = PreSamplex(qubit_map={qreg[0]: 0, qreg[1]: 1})
        node_id = pre_samplex.graph.add_node(
            PreCollect(qubit_idxs, Direction.LEFT, RzSxSynth(), [])
        )

        pre_samplex.add_dangler([0], node_id, DanglerType.REQUIRED)
        pre_samplex.add_dangler([1], node_id, DanglerType.OPTIONAL)

        # Only REQUIRED
        match = DanglerMatch(dangler_type=DanglerType.REQUIRED)
        qubit_0 = QubitIndicesPartition.from_elements([0])
        assert list(pre_samplex.find_danglers(match, qubit_0)) == [(node_id, qubit_0)]
        # Only OPTIONAL
        match = DanglerMatch(dangler_type=DanglerType.OPTIONAL)
        qubit_1 = QubitIndicesPartition.from_elements([1])
        assert list(pre_samplex.find_danglers(match, qubit_1)) == [(node_id, qubit_1)]
        # All
        match = DanglerMatch(dangler_type=None)
        assert list(pre_samplex.find_danglers(match, qubit_0)) == [(node_id, qubit_0)]
        assert list(pre_samplex.find_danglers(match, qubit_idxs)) == [(node_id, qubit_idxs)]

    def test_add_then_find_remove_danglers(self):
        """Test that added danglers are then found and removed"""
        qreg = QuantumRegister(2)
        qubit_idxs = QubitIndicesPartition.from_elements([0, 1])
        pre_samplex = PreSamplex(qubit_map={qreg[0]: 0, qreg[1]: 1})
        node_id = pre_samplex.graph.add_node(
            PreCollect(qubit_idxs, Direction.LEFT, RzSxSynth(), [])
        )

        pre_samplex.add_dangler([0], node_id, DanglerType.REQUIRED)
        pre_samplex.add_dangler([1], node_id, DanglerType.OPTIONAL)

        # REQUIRED
        match = DanglerMatch(dangler_type=DanglerType.REQUIRED)
        qubit_0 = QubitIndicesPartition.from_elements([0])
        assert list(pre_samplex.find_then_remove_danglers(match, qubit_0)) == [(node_id, qubit_0)]
        assert list(pre_samplex.find_then_remove_danglers(match, qubit_0)) == []
        # Optional
        match = DanglerMatch(dangler_type=DanglerType.OPTIONAL)
        qubit_1 = QubitIndicesPartition.from_elements([1])
        assert list(pre_samplex.find_then_remove_danglers(match, qubit_1)) == [(node_id, qubit_1)]
        assert list(pre_samplex.find_then_remove_danglers(match, qubit_1)) == []


class TestBuildPreSamplex:
    """Test the functions used to build the pre-samplex."""

    def test_collect_left_emit(self):
        """Test collecting an emit on the left side of a box."""
        qreg = QuantumRegister(2)
        subsystems = QubitPartition.from_elements(qreg)

        pre_samplex = PreSamplex(qubit_map={qreg[0]: 0, qreg[1]: 1})
        pre_samplex.add_collect(subsystems, RzSxSynth(), [])
        pre_samplex.add_emit_twirl(subsystems, PauliRegister)
        pre_samplex.add_collect(subsystems, RzSxSynth(), [])

        subsystem_idxs = QubitIndicesPartition.from_elements([0, 1])
        expected_nodes = [
            PreCollect(subsystem_idxs, Direction.BOTH, RzSxSynth(), []),
            PreEmit(subsystem_idxs, Direction.BOTH, PauliRegister),
            PreCollect(subsystem_idxs, Direction.BOTH, RzSxSynth(), []),
        ]

        assert pre_samplex.graph.nodes() == expected_nodes

    def test_emit_left_errors(self):
        """Test that adding an emit without collect raises an error."""
        qreg = QuantumRegister(2)
        pre_samplex = PreSamplex(qubit_map={qreg[0]: 0, qreg[1]: 1})

        # Found an emission without a collector on subsystems {(0,), (1,)}
        emit_subsystems = QubitPartition.from_elements(qreg)
        with pytest.raises(
            SamplexBuildError, match=r"without a collector on subsystems \{\(0,\), \(1,\)\}"
        ):
            pre_samplex.add_emit_twirl(emit_subsystems, PauliRegister)

        smaller_subsystems = QubitPartition.from_elements(qreg[:1])
        pre_samplex.add_collect(smaller_subsystems, RzSxSynth(), [])
        with pytest.raises(
            SamplexBuildError, match=r"without a collector on subsystems \{\(1,\)\}"
        ):
            pre_samplex.add_emit_twirl(emit_subsystems, PauliRegister)

    def test_emit_basis_errors(self):
        """Test that adding emit basis with same name but different length errors."""
        qreg = QuantumRegister(2)
        pre_samplex = PreSamplex(qubit_map={qreg[0]: 0, qreg[1]: 1})
        pre_samplex.add_emit_meas_basis_transform(QubitPartition.from_elements(qreg[:1]), "meas")

        with pytest.raises(SamplexBuildError, match=r"Cannot add basis transform"):
            pre_samplex.add_emit_meas_basis_transform(QubitPartition.from_elements(qreg), "meas")

        with pytest.raises(SamplexBuildError, match=r"Cannot add basis transform"):
            pre_samplex.add_emit_prep_basis_transform(QubitPartition.from_elements(qreg), "meas")

    def test_propagate_preceded_by_collect(self):
        """Test that add_propagate adds leftwards pre-propagate node."""
        qreg = QuantumRegister(2)
        subsystems = QubitPartition.from_elements(qreg)

        pre_samplex = PreSamplex(qubit_map={qreg[0]: 0, qreg[1]: 1})
        pre_samplex.add_collect(subsystems, RzSxSynth(), [])
        pre_samplex.add_propagate(CircuitInstruction(CXGate(), qreg), InstructionSpec())

        subsys_idxs = QubitIndicesPartition.from_elements([0, 1])
        assert pre_samplex.graph.nodes()[0] == PreCollect(
            subsys_idxs, Direction.BOTH, RzSxSynth(), []
        )
        assert pre_samplex.graph.nodes()[1] == PrePropagate(
            subsys_idxs, Direction.LEFT, CXGate(), [[0, 1]], {}
        )

        assert len(pre_samplex.graph.edges()) == 1

    def test_propagate_preceded_by_emit(self):
        """Test that add_propagate adds right pre-propagate node."""
        qreg = QuantumRegister(2)
        subsystems = QubitPartition.from_elements(qreg)

        pre_samplex = PreSamplex(qubit_map={qreg[0]: 0, qreg[1]: 1})
        pre_samplex.add_collect(subsystems, RzSxSynth(), [])
        pre_samplex.add_emit_twirl(subsystems, PauliRegister)
        pre_samplex.add_propagate(CircuitInstruction(CXGate(), qreg), InstructionSpec())

        subsys_idxs = QubitIndicesPartition.from_elements([0, 1])
        assert pre_samplex.graph.nodes()[0] == PreCollect(
            subsys_idxs, Direction.BOTH, RzSxSynth(), []
        )
        assert pre_samplex.graph.nodes()[1] == PreEmit(subsys_idxs, Direction.BOTH, PauliRegister)
        assert pre_samplex.graph.nodes()[2] == PrePropagate(
            subsys_idxs, Direction.RIGHT, CXGate(), [[0, 1]], {}
        )
        assert pre_samplex.graph.nodes()[3] == PrePropagate(
            subsys_idxs, Direction.LEFT, CXGate(), [[0, 1]], {}
        )

        assert len(pre_samplex.graph.edges()) == 3

    def test_propagate_errors_when_not_all_qubits_are_dangling(self):
        """Test that propagate errors when there are not enough dangling qubits."""
        qreg = QuantumRegister(2)

        pre_samplex = PreSamplex(qubit_map={qreg[0]: 0, qreg[1]: 1})
        pre_samplex.add_collect(QubitPartition.from_elements(qreg[:1]), RzSxSynth(), [])
        pre_samplex.add_emit_twirl(QubitPartition.from_elements(qreg[:1]), PauliRegister)
        with pytest.raises(SamplexBuildError, match="overlaps partially with .* left-to-right"):
            pre_samplex.add_propagate(CircuitInstruction(CXGate(), qreg), InstructionSpec())

        pre_samplex = PreSamplex(qubit_map={qreg[0]: 0, qreg[1]: 1})
        pre_samplex.add_collect(QubitPartition.from_elements(qreg[:1]), RzSxSynth(), [])
        with pytest.raises(SamplexBuildError, match="overlaps partially with .* collectors.* left"):
            pre_samplex.add_propagate(CircuitInstruction(CXGate(), qreg), InstructionSpec())

    def test_error_right_propagate_through_measurement(self):
        """Test that propagation through measurement to the right raises an error"""
        qreg = QuantumRegister(1)

        pre_samplex = PreSamplex(qubit_map={qreg[0]: 0})
        pre_samplex.add_collect(QubitPartition.from_elements(qreg), RzSxSynth(), [])
        pre_samplex.add_emit_twirl(QubitPartition.from_elements(qreg), PauliRegister)
        with pytest.raises(SamplexBuildError, match="Cannot propagate through measure instruction"):
            pre_samplex.add_propagate(CircuitInstruction(Measure(), qreg), InstructionSpec())

    def test_error_left_propagate_through_measurement(self):
        """Test that propagation through measurement to the left raises an error"""
        qreg = QuantumRegister(1)

        pre_samplex = PreSamplex(qubit_map={qreg[0]: 0})
        pre_samplex.add_collect(QubitPartition.from_elements(qreg), RzSxSynth(), [])
        pre_samplex.add_propagate(CircuitInstruction(Measure(), qreg), InstructionSpec())
        with pytest.raises(SamplexBuildError, match="Found an emission without a collector"):
            pre_samplex.add_emit_twirl(QubitPartition.from_elements(qreg), PauliRegister)

    def test_add_propagate_measurement(self):
        """Test that add_propagate on a measurement works when no virtual gate is met."""
        qreg = QuantumRegister(1)

        pre_samplex = PreSamplex(qubit_map={qreg[0]: 0})
        pre_samplex.add_collect(QubitPartition.from_elements(qreg), RzSxSynth(), [])
        pre_samplex.add_propagate(CircuitInstruction(Measure(), qreg), InstructionSpec())
        pre_samplex.add_collect(QubitPartition.from_elements(qreg), RzSxSynth(), [])
        pre_samplex.add_emit_twirl(QubitPartition.from_elements(qreg), PauliRegister)

        assert len(pre_samplex.graph.edges()) == 1
        assert len(pre_samplex.graph.nodes()) == 3

    def test_add_z2_collect(self):
        """Test that adding a Z2 collect adds the node and edges to the graph."""
        qreg = QuantumRegister(2)
        creg = ClassicalRegister(2)

        state = PreSamplex(qubit_map={qreg[0]: 0, qreg[1]: 1}, cregs=[creg])
        state.add_collect(QubitPartition.from_elements(qreg), RzSxSynth(), [])
        state.add_emit_twirl(QubitPartition.from_elements(qreg), PauliRegister)
        state.add_propagate(CircuitInstruction(XGate(), [qreg[0]]), InstructionSpec())
        state.add_z2_collect(QubitPartition.from_elements(qreg), [0, 1])

        subsys_idxs = QubitIndicesPartition.from_elements([0, 1])
        assert state.graph.nodes()[-3] == PrePropagate(
            QubitIndicesPartition.from_elements([0]), Direction.RIGHT, XGate(), [[0]], {}
        )
        assert state.graph.nodes()[-2] == PrePropagate(
            QubitIndicesPartition.from_elements([0]), Direction.LEFT, XGate(), [[0]], {}
        )
        assert state.graph.nodes()[-1] == PreZ2Collect(
            subsys_idxs, {creg.name: [0, 1]}, {creg.name: [0, 1]}
        )

    def test_add_z2_collect_errors(self):
        """Test that adding a Z2 collect raises errors."""
        qreg = QuantumRegister(2)
        creg = ClassicalRegister(2)

        state = PreSamplex(qubit_map={qreg[0]: 0, qreg[1]: 1}, cregs=[creg])
        state.add_collect(QubitPartition.from_elements(qreg), RzSxSynth(), [])
        state.add_emit_twirl(QubitPartition.from_elements([qreg[0]]), PauliRegister)
        with pytest.raises(
            SamplexBuildError, match="some qubits are missing corresponding emissions"
        ):
            state.add_z2_collect(QubitPartition.from_elements(qreg), [0, 1])

        with pytest.raises(SamplexBuildError, match="Number of qubits != number of clbits"):
            state.add_z2_collect(QubitPartition.from_elements(qreg), [0, 1, 2])


class TestHelpersAttributes:
    """Test helper and attributes."""

    def test_sorted_predecessor_idxs(self):
        """Test the sorted_predecessor_idxs method."""
        q0, q1, q2, q3 = QuantumRegister(4)
        subsystems = QubitIndicesPartition(1, ((q0,), (q1,), (q2,), (q3,)))
        subsystems0 = QubitIndicesPartition(1, ((q0,), (q1,)))
        subsystems1 = QubitIndicesPartition(1, ((q2,), (q3,)))

        pre_samplex = PreSamplex(qubit_map={q0: 0, q1: 1, q2: 2, q3: 3})
        pre_samplex.add_collect(subsystems, RzSxSynth(), [])
        prep_idx0 = pre_samplex.add_emit_prep_basis_transform(subsystems, "prepare")
        emit_idx0 = pre_samplex.add_emit_twirl(subsystems, PauliRegister)
        collect_idx1 = pre_samplex.add_collect(subsystems, RzSxSynth(), [])
        meas_idx0 = pre_samplex.add_emit_meas_basis_transform(subsystems, "measure")
        emit_idx10 = pre_samplex.add_emit_twirl(subsystems0, PauliRegister)
        emit_idx11 = pre_samplex.add_emit_twirl(subsystems1, PauliRegister)
        collect_idx2 = pre_samplex.add_collect(subsystems, RzSxSynth(), [])

        order = {emit_idx0: 1, prep_idx0: 0, emit_idx10: 2, emit_idx11: 3, meas_idx0: 4}
        assert pre_samplex.sorted_predecessor_idxs(collect_idx1, order) == [
            emit_idx11,
            emit_idx10,
            meas_idx0,
            prep_idx0,
            emit_idx0,
        ]

        order = {emit_idx0: 50, prep_idx0: 51, emit_idx10: 4, emit_idx11: 2, meas_idx0: 1}
        assert pre_samplex.sorted_predecessor_idxs(collect_idx1, order) == [
            emit_idx10,
            emit_idx11,
            meas_idx0,
            prep_idx0,
            emit_idx0,
        ]

        order = {emit_idx0: 50, emit_idx10: 4, emit_idx11: 2}
        assert pre_samplex.sorted_predecessor_idxs(collect_idx2, order) == [emit_idx11, emit_idx10]


class TestFinalize:
    """Test the finalize method."""

    def test_finalize_validates_rightward_danglers(self):
        """Test that we raise when the graph has unterminated nodes."""
        qreg = QuantumRegister(4)
        subsystems = QubitPartition.from_elements(qreg)
        subsystems0 = QubitPartition.from_elements(qreg[:2])
        subsystems1 = QubitPartition.from_elements(qreg[2:])

        pre_samplex = PreSamplex(qubit_map={qubit: idx for idx, qubit in enumerate(qreg)})
        pre_samplex.add_collect(subsystems, RzSxSynth(), [])
        pre_samplex.add_emit_twirl(subsystems0, VirtualType.PAULI)
        pre_samplex.add_collect(subsystems, RzSxSynth(), [])
        pre_samplex.add_emit_twirl(subsystems1, VirtualType.PAULI)

        with pytest.raises(SamplexBuildError, match=r"unterminated .* on qubit indices \[2, 3\]"):
            pre_samplex.finalize()

    def test_finalize_prunes_unreachable_nodes(self):
        """Test the finalize method prunes unreachable nodes."""
        qreg = QuantumRegister(2)
        subsystems = QubitPartition.from_elements(qreg)

        pre_samplex = PreSamplex(qubit_map={qubit: idx for idx, qubit in enumerate(qreg)})
        pre_samplex.add_collect(subsystems, RzSxSynth(), np.array([[0, 1, 2], [3, 4, 5]]))
        pre_samplex.add_propagate(CircuitInstruction(CXGate(), qreg), InstructionSpec())
        pre_samplex.finalize()
        assert not pre_samplex.graph.nodes()

        pre_samplex = PreSamplex(qubit_map={qubit: idx for idx, qubit in enumerate(qreg)})
        pre_samplex.add_collect(subsystems, RzSxSynth(), np.array([[0, 1, 2], [3, 4, 5]]))
        pre_samplex.add_emit_twirl(subsystems, VirtualType.PAULI)
        pre_samplex.add_collect(subsystems, RzSxSynth(), np.array([[0, 1, 2], [3, 4, 5]]))
        pre_samplex.add_propagate(CircuitInstruction(CXGate(), qreg), InstructionSpec())
        assert len(pre_samplex.graph) == 4
        assert len(pre_samplex.graph.edges()) == 3

        pre_samplex.finalize()
        assert len(pre_samplex.graph) == 3
        assert len(pre_samplex.graph.edges()) == 2


class TestPrePropagateClustering:
    """Test the `_cluster_pre_propagate_nodes` function."""

    def test_nodes_clustered(self):
        """Test that nodes are clustered"""
        circ = QuantumCircuit(6)
        circ.cx(0, 1)
        circ.cx(2, 3)
        circ.sx(4)
        circ.sx(5)
        subsystems = QubitPartition(1, ((q,) for q in circ.qregs[0]))

        pre_samplex = PreSamplex(qubit_map={q: idx for idx, q in enumerate(circ.qregs[0])})
        pre_samplex.add_collect(subsystems, RzSxSynth(), [])
        for instr in circ:
            pre_samplex.add_propagate(instr, InstructionSpec())
        pre_samplex.add_emit_twirl(subsystems, PauliRegister)

        clusters = pre_samplex._cluster_pre_propagate_nodes([0, 1, 2, 3, 4, 5])  # noqa: SLF001
        assert clusters == [[1, 2], [3, 4]]

    def test_nodes_different_modes(self):
        """Test that nodes are not clustered if the mode is different"""
        circ = QuantumCircuit(4)
        circ.cx(0, 1)
        circ.cx(2, 3)
        subsystems = QubitPartition(1, ((q,) for q in circ.qregs[0]))

        pre_samplex = PreSamplex(qubit_map={q: idx for idx, q in enumerate(circ.qregs[0])})
        pre_samplex.add_collect(subsystems, RzSxSynth(), [])
        pre_samplex.add_propagate(circ[0], InstructionSpec(mode=InstructionMode.MULTIPLY))
        pre_samplex.add_propagate(circ[1], InstructionSpec(mode=InstructionMode.PROPAGATE))
        pre_samplex.add_emit_twirl(subsystems, PauliRegister)

        clusters = pre_samplex._cluster_pre_propagate_nodes([0, 1, 2, 3])  # noqa: SLF001
        assert clusters == [[1], [2]]

    def test_nodes_different_predecessors(self):
        """Test that nodes are not clustered if they don't share predecessors."""
        circ = QuantumCircuit(4)
        circ.cx(0, 1)
        circ.cx(2, 3)
        subsystems = QubitPartition(1, ((q,) for q in circ.qregs[0]))

        pre_samplex = PreSamplex(qubit_map={q: idx for idx, q in enumerate(circ.qregs[0])})
        pre_samplex.add_collect(subsystems, RzSxSynth(), [])
        pre_samplex.add_collect(
            QubitPartition(1, ((circ.qubits[2],), (circ.qubits[3],))), RzSxSynth(), []
        )
        for instr in circ:
            pre_samplex.add_propagate(instr, InstructionSpec())
        pre_samplex.add_emit_twirl(
            QubitPartition(1, ((circ.qubits[0],), (circ.qubits[1],))), PauliRegister
        )
        pre_samplex.add_emit_twirl(
            QubitPartition(1, ((circ.qubits[2],), (circ.qubits[3],))), PauliRegister
        )

        clusters = pre_samplex._cluster_pre_propagate_nodes([0, 1, 2, 3])  # noqa: SLF001
        assert clusters == [[2], [3]]

    def test_nodes_different_operation(self):
        """Test that nodes are not clustered if they don't share operation."""
        circ = QuantumCircuit(4)
        circ.cx(0, 1)
        circ.cz(2, 3)
        subsystems = QubitPartition(1, ((q,) for q in circ.qregs[0]))

        pre_samplex = PreSamplex(qubit_map={q: idx for idx, q in enumerate(circ.qregs[0])})
        pre_samplex.add_collect(subsystems, RzSxSynth(), [])
        for instr in circ:
            pre_samplex.add_propagate(instr, InstructionSpec())
        pre_samplex.add_emit_twirl(subsystems, PauliRegister)

        clusters = pre_samplex._cluster_pre_propagate_nodes([0, 1, 2, 3])  # noqa: SLF001
        assert clusters == [[1], [2]]

    def test_nodes_overlaping_qubits(self):
        """Test that nodes are not clustered if they share qubits."""
        circ = QuantumCircuit(3)
        circ.cx(0, 1)
        circ.cx(1, 2)
        subsystems = QubitPartition(1, ((q,) for q in circ.qregs[0]))

        pre_samplex = PreSamplex(qubit_map={q: idx for idx, q in enumerate(circ.qregs[0])})
        pre_samplex.add_collect(subsystems, RzSxSynth(), [])
        for instr in circ:
            pre_samplex.add_propagate(instr, InstructionSpec())
        pre_samplex.add_emit_twirl(subsystems, PauliRegister)

        clusters = pre_samplex._cluster_pre_propagate_nodes([0, 1, 2, 3])  # noqa: SLF001
        assert clusters == [[1], [2]]


class TestMergeParallelPrePropagateNodes:
    """Test the `merge_parallel_pre_propagate_nodes` function."""

    def test_pre_samplex_with_mergeable_pre_propagates(self):
        """Test propagating an instruction on disjoint qubits merges nodes together."""
        box = QuantumCircuit(4)
        box.cx(0, 1)
        box.cx(2, 3)
        subsystems = QubitPartition(1, ((q,) for q in box.qregs[0]))

        pre_samplex = PreSamplex(qubit_map={q: idx for idx, q in enumerate(box.qregs[0])})
        pre_samplex.add_collect(subsystems, RzSxSynth(), [])
        for instr in box:
            pre_samplex.add_propagate(instr, InstructionSpec())
        pre_samplex.add_emit_twirl(subsystems, PauliRegister)
        for instr in box:
            pre_samplex.add_propagate(instr, InstructionSpec())
        pre_samplex.add_collect(subsystems, RzSxSynth(), [])
        pre_samplex.prune_prenodes_unreachable_from_emission()

        assert len(pre_samplex.graph.nodes()) == 7

        pre_samplex.merge_parallel_pre_propagate_nodes()
        assert len(pre_samplex.graph.nodes()) == 5

        node_idxs = topological_sort(pre_samplex.graph)

        assert isinstance(pre_samplex.graph[node_idxs[0]], PreEmit)
        assert isinstance(pre_samplex.graph[node_idxs[1]], PrePropagate)
        assert isinstance(pre_samplex.graph[node_idxs[2]], PrePropagate)
        assert isinstance(pre_samplex.graph[node_idxs[3]], PreCollect)
        assert isinstance(pre_samplex.graph[node_idxs[4]], PreCollect)

        assert pre_samplex.graph[node_idxs[1]].subsystems.all_elements == {0, 1, 2, 3}
        assert pre_samplex.graph[node_idxs[2]].subsystems.all_elements == {0, 1, 2, 3}

    def test_pre_samplex_with_no_mergeable_pre_propagates(self):
        """Test propagating an instruction on overlapping qubits adds a new propagate node."""
        box = QuantumCircuit(4)
        box.cx(0, 1)
        box.cx(1, 2)
        subsystems = QubitPartition(1, ((q,) for q in box.qregs[0]))

        pre_samplex = PreSamplex(qubit_map={q: idx for idx, q in enumerate(box.qregs[0])})
        pre_samplex.add_collect(subsystems, RzSxSynth(), [])
        for instr in box:
            pre_samplex.add_propagate(instr, InstructionSpec())
        pre_samplex.add_emit_twirl(subsystems, PauliRegister)
        for instr in box:
            pre_samplex.add_propagate(instr, InstructionSpec())
        pre_samplex.add_collect(subsystems, RzSxSynth(), [])
        pre_samplex.prune_prenodes_unreachable_from_emission()

        assert len(pre_samplex.graph.nodes()) == 7

        pre_samplex.merge_parallel_pre_propagate_nodes()
        assert len(pre_samplex.graph.nodes()) == 7

        node_idxs = topological_sort(pre_samplex.graph)
        assert isinstance(pre_samplex.graph[node_idxs[0]], PreEmit)
        assert isinstance(pre_samplex.graph[node_idxs[1]], PrePropagate)
        assert isinstance(pre_samplex.graph[node_idxs[2]], PrePropagate)
        assert isinstance(pre_samplex.graph[node_idxs[3]], PreCollect)
        assert isinstance(pre_samplex.graph[node_idxs[4]], PrePropagate)
        assert isinstance(pre_samplex.graph[node_idxs[5]], PrePropagate)
        assert isinstance(pre_samplex.graph[node_idxs[6]], PreCollect)

        assert pre_samplex.graph[node_idxs[1]].subsystems.all_elements == {0, 1}
        assert pre_samplex.graph[node_idxs[1]].partition.all_elements == {0, 1}

        assert pre_samplex.graph[node_idxs[2]].subsystems.all_elements == {1, 2}
        assert pre_samplex.graph[node_idxs[2]].partition.all_elements == {0, 1}

        assert pre_samplex.graph[node_idxs[4]].subsystems.all_elements == {1, 2}
        assert pre_samplex.graph[node_idxs[4]].partition.all_elements == {0, 1}

        assert pre_samplex.graph[node_idxs[5]].subsystems.all_elements == {0, 1}
        assert pre_samplex.graph[node_idxs[5]].partition.all_elements == {0, 1}

    def test_pre_samplex_with_mergeable_pre_propagates_in_series(self):
        box1 = QuantumCircuit(4)
        box1.cx(0, 1)
        box1.cx(2, 3)
        box1.cx(0, 1)
        box1.cx(2, 3)
        box1.cx(0, 1)
        box1.cx(2, 3)

        subsystems = QubitPartition(1, ((q,) for q in box1.qregs[0]))

        pre_samplex = PreSamplex(qubit_map={q: idx for idx, q in enumerate(box1.qregs[0])})
        pre_samplex.add_collect(subsystems, RzSxSynth(), [])
        for instr in box1:
            pre_samplex.add_propagate(instr, InstructionSpec())
        pre_samplex.add_emit_twirl(subsystems, PauliRegister)
        pre_samplex.prune_prenodes_unreachable_from_emission()

        assert len(pre_samplex.graph.nodes()) == 8

        pre_samplex.merge_parallel_pre_propagate_nodes()
        assert len(pre_samplex.graph.nodes()) == 5

        node_idxs = topological_sort(pre_samplex.graph)
        assert isinstance(pre_samplex.graph[node_idxs[0]], PreEmit)
        assert isinstance(pre_samplex.graph[node_idxs[1]], PrePropagate)
        assert isinstance(pre_samplex.graph[node_idxs[2]], PrePropagate)
        assert isinstance(pre_samplex.graph[node_idxs[3]], PrePropagate)
        assert isinstance(pre_samplex.graph[node_idxs[4]], PreCollect)

        assert pre_samplex.graph[node_idxs[1]].subsystems.all_elements == {0, 1, 2, 3}
        assert pre_samplex.graph[node_idxs[1]].partition.all_elements == {0, 1, 2, 3}

        assert pre_samplex.graph[node_idxs[2]].subsystems.all_elements == {0, 1, 2, 3}
        assert pre_samplex.graph[node_idxs[2]].partition.all_elements == {0, 1, 2, 3}

        assert pre_samplex.graph[node_idxs[3]].subsystems.all_elements == {0, 1, 2, 3}
        assert pre_samplex.graph[node_idxs[3]].partition.all_elements == {0, 1, 2, 3}

    def test_partitions_are_rescaled_correctly(self):
        """Test that partitions are rescaled correctly."""
        box = QuantumCircuit(8)
        box.cx(1, 2)
        box.cx(0, 3)
        box.cx(7, 4)

        subsystems = QubitPartition(1, ((q,) for q in box.qregs[0]))

        pre_samplex = PreSamplex(qubit_map={q: idx for idx, q in enumerate(box.qregs[0])})
        pre_samplex.add_collect(subsystems, RzSxSynth(), [])
        for instr in box:
            pre_samplex.add_propagate(instr, InstructionSpec())
        pre_samplex.add_emit_twirl(subsystems, PauliRegister)

        pre_samplex.prune_prenodes_unreachable_from_emission()
        pre_samplex.merge_parallel_pre_propagate_nodes()

        node_idxs = topological_sort(pre_samplex.graph)
        assert isinstance(pre_samplex.graph[node_idxs[1]], PrePropagate)

        qubit_idxs = QubitIndicesPartition(1, [(7,), (4,), (1,), (2,), (0,), (3,)])
        assert pre_samplex.graph[node_idxs[1]].subsystems == qubit_idxs

        partition = SubsystemIndicesPartition(2, [(0, 1), (2, 3), (4, 5)])
        assert pre_samplex.graph[node_idxs[1]].partition == partition

    def test_unsupported_propagate_error(self):
        """Test that add_propagate_node errors when trying to add an unsupported operation."""
        circuit = QuantumCircuit(2)
        circuit.cx(0, 1)
        subsystems = QubitPartition(1, ((q,) for q in circuit.qregs[0]))

        pre_samplex = PreSamplex(qubit_map={q: idx for idx, q in enumerate(circuit.qregs[0])})
        pre_samplex.add_collect(subsystems, RzSxSynth(), np.arange(6).reshape(2, 3))
        pre_samplex.add_propagate(
            next(iter(circuit)), InstructionSpec(mode=InstructionMode.MULTIPLY)
        )
        pre_samplex.add_emit_twirl(subsystems, VirtualType.PAULI)
        pre_samplex.add_collect(subsystems, RzSxSynth(), np.arange(6).reshape(2, 3))

        with pytest.raises(
            SamplexBuildError,
            match="Encountered unsupported cx propragation with mode InstructionMode.MULTIPLY.",
        ):
            pre_samplex.finalize()

    def test_if_else_with_mergable_preedges(self):
        """Test that merging of PreEdges maintains their force_register_copy property.

        Because it is a bit difficult to do by hand, we use the full pre_build.
        """
        circuit = QuantumCircuit(2, 1)
        circuit.measure(0, 0)
        with circuit.box([Twirl(dressing="left")]):
            with circuit.if_test((circuit.clbits[0], 1)) as _else:
                circuit.x(0)
                circuit.x(1)
            with _else:
                circuit.sx(0)
                circuit.sx(1)
        with circuit.box([Twirl(dressing="right")]):
            circuit.noop(0, 1)

        _, pre_samplex = pre_build(circuit)
        pre_samplex.merge_parallel_pre_propagate_nodes()
        graph = pre_samplex.graph
        for emit_node in [6, 7]:
            assert not graph.get_edge_data(emit_node, 4).force_register_copy
            assert graph.get_edge_data(emit_node, 9).force_register_copy
        assert graph[4].operation.name == "x"
        assert graph[9].operation.name == "sx"
        assert graph[9].subsystems.all_elements == {0, 1}


class TestDraw:
    """Test the ``draw`` method."""

    @pytest.mark.skipif(not HAS_PLOTLY, reason="plotly is not installed")
    def test_draw(self, save_plot):
        """Test the ``draw`` method."""
        box = QuantumCircuit(4)
        box.cx(0, 1)
        box.cx(1, 2)
        subsystems = QubitPartition.from_elements(box.qubits)

        pre_samplex = PreSamplex(qubit_map={q: idx for idx, q in enumerate(box.qregs[0])})
        pre_samplex.add_collect(subsystems, RzSxSynth(), [])
        for instr in box:
            pre_samplex.add_propagate(instr, InstructionSpec())
        pre_samplex.add_emit_twirl(subsystems, VirtualType.PAULI)
        for instr in box:
            pre_samplex.add_propagate(instr, InstructionSpec())
        pre_samplex.add_collect(subsystems, RzSxSynth(), [])

        save_plot(pre_samplex.draw())
