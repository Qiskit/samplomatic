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

"""Tests for samplomatic.stratification.conversion."""

import pytest
from qiskit.circuit import BoxOp, ClassicalRegister, Parameter, QuantumCircuit, QuantumRegister
from qiskit.circuit.classical import expr
from qiskit.converters import circuit_to_dag

from samplomatic.stratification import (
    Layer,
    Stratification,
    dag_to_instance,
    greedy_stratify,
    stratification_to_dag,
    stratify_mixed,
    stratify_separate,
)


def _to_dag(qc: QuantumCircuit):
    return circuit_to_dag(qc)


def _dag_op_names(dag):
    """Return the list of top-level op names in topological order."""
    return [n.name for n in dag.topological_op_nodes()]


def _box_contents(dag):
    """Return the list of frozensets of op names inside each box, in DAG order."""
    return [
        frozenset(d.operation.name for d in n.op.body.data)
        for n in dag.topological_op_nodes()
        if n.name == "box"
    ]


class TestEmptyDag:
    def test_empty_round_trip(self):
        qc = QuantumCircuit(3)
        instance, ctx = dag_to_instance(_to_dag(qc))
        assert instance.num_edges == 0
        assert instance.num_vertices == 3
        assert ctx.edge_ops == ()
        assert ctx.bare_ops == ()
        strat = Stratification(instance, [])
        out_dag = stratification_to_dag(strat, ctx)
        assert list(out_dag.topological_op_nodes()) == []
        assert len(out_dag.qubits) == 3


class TestSingle2qGate:
    def test_cx_single(self):
        qc = QuantumCircuit(2)
        qc.cx(0, 1)
        instance, ctx = dag_to_instance(_to_dag(qc))
        assert instance.num_edges == 1
        assert instance.hypergraph.edges == (frozenset({0, 1}),)
        assert instance.labels == (("cx", (), (0, 1)),)
        assert len(ctx.edge_ops) == 1
        assert ctx.edge_ops[0].qargs == (0, 1)
        assert ctx.edge_ops[0].op.name == "cx"


class TestLabels:
    def test_cz_symmetric_canonicalised(self):
        qc1 = QuantumCircuit(2)
        qc1.cz(0, 1)
        qc2 = QuantumCircuit(2)
        qc2.cz(1, 0)
        i1, _ = dag_to_instance(_to_dag(qc1))
        i2, _ = dag_to_instance(_to_dag(qc2))
        assert i1.labels[0] == i2.labels[0]
        assert i1.labels[0] == ("cz", (), frozenset({0, 1}))

    def test_cx_asymmetric_distinguished(self):
        qc1 = QuantumCircuit(2)
        qc1.cx(0, 1)
        qc2 = QuantumCircuit(2)
        qc2.cx(1, 0)
        i1, _ = dag_to_instance(_to_dag(qc1))
        i2, _ = dag_to_instance(_to_dag(qc2))
        assert i1.labels[0] != i2.labels[0]
        assert i1.labels[0] == ("cx", (), (0, 1))
        assert i2.labels[0] == ("cx", (), (1, 0))

    def test_rzz_concrete_params_distinguished(self):
        qc1 = QuantumCircuit(2)
        qc1.rzz(0.1, 0, 1)
        qc2 = QuantumCircuit(2)
        qc2.rzz(0.2, 0, 1)
        i1, _ = dag_to_instance(_to_dag(qc1))
        i2, _ = dag_to_instance(_to_dag(qc2))
        assert i1.labels[0] != i2.labels[0]

    def test_rzz_distinct_parameters_distinguished(self):
        a, b = Parameter("a"), Parameter("b")
        qc1 = QuantumCircuit(2)
        qc1.rzz(a, 0, 1)
        qc2 = QuantumCircuit(2)
        qc2.rzz(b, 0, 1)
        i1, _ = dag_to_instance(_to_dag(qc1))
        i2, _ = dag_to_instance(_to_dag(qc2))
        assert i1.labels[0] != i2.labels[0]

    def test_cx_different_qubits_distinguished(self):
        """cx(0,1) and cx(2,3) must produce distinct labels."""
        qc = QuantumCircuit(4)
        qc.cx(0, 1)
        qc.cx(2, 3)
        instance, _ = dag_to_instance(_to_dag(qc))
        assert instance.labels[0] != instance.labels[1]
        assert instance.labels[0] == ("cx", (), (0, 1))
        assert instance.labels[1] == ("cx", (), (2, 3))

    def test_rzz_same_parameter_shared_label(self):
        a = Parameter("a")
        qc1 = QuantumCircuit(2)
        qc1.rzz(a, 0, 1)
        qc2 = QuantumCircuit(2)
        qc2.rzz(a, 0, 1)
        i1, _ = dag_to_instance(_to_dag(qc1))
        i2, _ = dag_to_instance(_to_dag(qc2))
        assert i1.labels[0] == i2.labels[0]


class TestPrecedence:
    def test_disjoint_no_arcs(self):
        qc = QuantumCircuit(4)
        qc.cx(0, 1)
        qc.cx(2, 3)
        instance, _ = dag_to_instance(_to_dag(qc))
        assert instance.precedence_arcs() == frozenset()

    def test_cz_network_all_incomparable(self):
        # All CZs commute pairwise.
        qc = QuantumCircuit(3)
        qc.cz(0, 1)
        qc.cz(0, 2)
        qc.cz(1, 2)
        instance, _ = dag_to_instance(_to_dag(qc))
        assert instance.precedence_arcs() == frozenset()

    def test_diagonal_1q_does_not_block(self):
        qc = QuantumCircuit(3)
        qc.cz(0, 1)
        qc.rz(0.5, 0)
        qc.cz(0, 2)
        instance, _ = dag_to_instance(_to_dag(qc))
        assert instance.precedence_arcs() == frozenset()

    def test_non_commuting_1q_blocks(self):
        qc = QuantumCircuit(3)
        qc.cz(0, 1)
        qc.rx(0.5, 0)
        qc.cz(0, 2)
        instance, _ = dag_to_instance(_to_dag(qc))
        assert instance.precedence_arcs() == frozenset({(0, 1)})

    def test_same_control_cx_commute(self):
        qc = QuantumCircuit(3)
        qc.cx(0, 1)
        qc.cx(0, 2)
        instance, _ = dag_to_instance(_to_dag(qc))
        assert instance.precedence_arcs() == frozenset()

    def test_target_to_control_cx_blocks(self):
        # cx(0,1) target=q1 then cx(1,2) control=q1: do not commute.
        qc = QuantumCircuit(3)
        qc.cx(0, 1)
        qc.cx(1, 2)
        instance, _ = dag_to_instance(_to_dag(qc))
        assert instance.precedence_arcs() == frozenset({(0, 1)})

    def test_transitive_arcs_preserved(self):
        # cx(0,1) ; cx(1,2) ; cx(2,3) — chain of conflicts; the precedence
        # is reduced to the Hasse diagram by StratificationInstance.
        qc = QuantumCircuit(4)
        qc.cx(0, 1)
        qc.cx(1, 2)
        qc.cx(2, 3)
        instance, _ = dag_to_instance(_to_dag(qc))
        # Hasse diagram: 0->1->2 (transitive 0->2 reduced away).
        assert instance.precedence_arcs() == frozenset({(0, 1), (1, 2)})

    def test_non_monotonic_commutation_on_shared_qubit(self):
        """Earlier non-commuter must be recorded even when shadowed by a commuter.

        Reproduces the trotter_chain bug:
        - rzz(0,1)  : edge 0
        - rzz(1,2)  : edge 1
        - rxx(0,1)  : edge 2   (commutes with rzz(0,1) on same pair)
        - ryy(1,2)  : edge 3

        On q1 the walk back from edge 3 first meets rxx(0,1)=edge 2 — a
        non-commuter on q1 — and then rzz(0,1)=edge 0, also a non-commuter
        on q1.  Because rzz(0,1) and rxx(0,1) commute (same pair, two
        anti-commutations cancel), no arc 0->2 exists; the order 0 < 3
        must therefore be recorded directly by the walk-back.
        """
        qc = QuantumCircuit(3)
        qc.rzz(0.1, 0, 1)
        qc.rzz(0.1, 1, 2)
        qc.rxx(0.1, 0, 1)
        qc.ryy(0.1, 1, 2)
        instance, _ = dag_to_instance(_to_dag(qc))
        # Edges in order of appearance: 0=rzz(0,1), 1=rzz(1,2), 2=rxx(0,1), 3=ryy(1,2).
        assert instance.is_comparable(0, 3)
        assert 0 in instance.predecessors(3)


class TestRoundTripBareOps:
    def test_bare_1q_anchor_placement(self):
        qc = QuantumCircuit(3)
        qc.rz(0.1, 0)
        qc.cx(0, 1)
        qc.rz(0.2, 1)
        qc.cx(0, 2)
        qc.rz(0.3, 0)
        instance, ctx = dag_to_instance(_to_dag(qc))
        # Two CXs share q0 with same control => no arcs.
        assert instance.precedence_arcs() == frozenset()
        # bare op anchors:
        anchors = [b.anchors for b in ctx.bare_ops]
        # rz(0): no preceding edge on q0 => (None,)
        # rz(1): preceding edge on q1 is edge 0 => (0,)
        # rz(0): preceding edge on q0 is edge 1 => (1,)
        assert (None,) in anchors
        assert (0,) in anchors
        assert (1,) in anchors

        strat = Stratification(instance, [Layer(instance, [0]), Layer(instance, [1])])
        out_dag = stratification_to_dag(strat, ctx)
        names = [n.name for n in out_dag.topological_op_nodes()]
        # Expected: rz, box, rz, box, rz
        assert names == ["rz", "box", "rz", "box", "rz"]


class TestLayerBodyShape:
    def test_two_disjoint_edges_in_one_layer(self):
        qc = QuantumCircuit(4)
        qc.cx(0, 1)
        qc.cx(2, 3)
        instance, ctx = dag_to_instance(_to_dag(qc))
        # Disjoint edges => no precedence => can co-occur in a single layer.
        layer = Layer(instance, [0, 1])
        strat = Stratification(instance, [layer])
        out_dag = stratification_to_dag(strat, ctx)

        ops = list(out_dag.topological_op_nodes())
        assert len(ops) == 1
        box_node = ops[0]
        assert box_node.name == "box"
        box_op: BoxOp = box_node.op
        assert box_op.num_qubits == 4
        body_names = [ci.operation.name for ci in box_op.body.data]
        assert sorted(body_names) == ["cx", "cx"]
        # Outer qubits should be the four qubits in order.
        assert tuple(box_node.qargs) == tuple(ctx.qubits)


class TestRejections:
    def test_three_qubit_gate(self):
        qc = QuantumCircuit(3)
        qc.ccx(0, 1, 2)
        with pytest.raises(ValueError, match="3 qubits"):
            dag_to_instance(_to_dag(qc))

    def test_unknown_gate(self):
        import numpy as np

        qc = QuantumCircuit(1)
        # An arbitrary 1q unitary not in our supported set.
        u = np.array([[1, 0], [0, 1]])
        qc.unitary(u, [0])
        with pytest.raises(ValueError, match="not in the supported set"):
            dag_to_instance(_to_dag(qc))

    def test_delay_rejected(self):
        qc = QuantumCircuit(1)
        qc.delay(10, 0)
        with pytest.raises(ValueError, match="not in the supported set"):
            dag_to_instance(_to_dag(qc))

    def test_control_flow_rejected(self):
        qc = QuantumCircuit(2, 1)
        qc.measure(0, 0)
        with qc.if_test(expr.lift(qc.clbits[0])):
            qc.x(1)
        with pytest.raises(ValueError, match="[Cc]ontrol-flow"):
            dag_to_instance(_to_dag(qc))


class TestMeasureReset:
    def test_measure_round_trip(self):
        qc = QuantumCircuit(QuantumRegister(3, "q"), ClassicalRegister(1, "c"))
        qc.cx(0, 1)
        qc.measure(0, 0)
        qc.cx(0, 2)
        qc.reset(1)
        instance, ctx = dag_to_instance(_to_dag(qc))
        # measure on q0 doesn't commute with cx(0,2) => arc 0->1.
        assert instance.precedence_arcs() == frozenset({(0, 1)})

        # Both bare ops have edge 0 as anchor (cx(0,1) is last edge on both q0 and q1).
        anchor_set = {b.op.name: b.anchors for b in ctx.bare_ops}
        assert anchor_set["measure"] == (0,)
        assert anchor_set["reset"] == (0,)

        strat = Stratification(instance, [Layer(instance, [0]), Layer(instance, [1])])
        out_dag = stratification_to_dag(strat, ctx)
        # Find the measure node and verify its clbit was preserved.
        measure_nodes = [n for n in out_dag.topological_op_nodes() if n.name == "measure"]
        assert len(measure_nodes) == 1
        assert measure_nodes[0].cargs == (ctx.clbits[0],)


class TestMixedExample:
    def test_full_round_trip_linearised(self):
        qc = QuantumCircuit(QuantumRegister(4, "q"), ClassicalRegister(2, "c"))
        qc.h(0)
        qc.cx(0, 1)
        qc.rz(0.1, 1)
        qc.cz(2, 3)
        qc.cx(1, 2)
        qc.measure(0, 0)
        instance, ctx = dag_to_instance(_to_dag(qc))

        # Edge ids in topo order: cx(0,1)=0, cz(2,3)=1, cx(1,2)=2. Both 0 and 1
        # share a qubit with edge 2 and do not commute with it, so 0 -> 2 and
        # 1 -> 2 are precedence arcs.
        assert (0, 2) in instance.precedence_arcs()
        assert (1, 2) in instance.precedence_arcs()

        # Layers: {0,1} (no shared vertex) then {2}.
        strat = Stratification(
            instance,
            [Layer(instance, [0, 1]), Layer(instance, [2])],
        )
        out_dag = stratification_to_dag(strat, ctx)

        # The output should have two box nodes and the bare ops in topo order.
        names = [n.name for n in out_dag.topological_op_nodes()]
        assert names.count("box") == 2
        assert "h" in names
        assert "rz" in names
        assert "measure" in names


class TestBarrier:
    def test_barrier_blocks_commuting_edges(self):
        # Two CZs on the same pair would commute (no arc) — but a barrier
        # between them must force a precedence arc.
        qc = QuantumCircuit(2)
        qc.cz(0, 1)
        qc.barrier(0, 1)
        qc.cz(0, 1)
        instance, _ = dag_to_instance(_to_dag(qc))
        assert instance.precedence_arcs() == frozenset({(0, 1)})

    def test_partial_barrier_isolates_qubits(self):
        # Barrier on (0,1) only constrains edges touching q0 or q1.
        # Edge ids are assigned in topological order: since the barrier shares
        # no wire with cz(2,3), the DAG topo order interleaves them — edges on
        # (0,1) get ids 0,1 and edges on (2,3) get ids 2,3.
        qc = QuantumCircuit(4)
        qc.cz(0, 1)
        qc.cz(2, 3)
        qc.barrier(0, 1)
        qc.cz(0, 1)
        qc.cz(2, 3)
        instance, _ = dag_to_instance(_to_dag(qc))
        arcs = instance.precedence_arcs()
        # Barrier on (0,1) forces an arc between the two cz(0,1) edges.
        assert (0, 1) in arcs
        # The two cz(2,3) edges commute (same gate, same pair) and the barrier
        # doesn't touch q2/q3, so no arc.
        assert (2, 3) not in arcs

    def test_wide_barrier_accepted(self):
        # Barrier on >2 qubits is accepted (unlike unitary ops on >2 qubits).
        qc = QuantumCircuit(5)
        qc.cx(0, 1)
        qc.barrier(0, 1, 2, 3, 4)
        qc.cx(3, 4)
        instance, ctx = dag_to_instance(_to_dag(qc))
        barrier_bare = [b for b in ctx.bare_ops if b.op.name == "barrier"]
        assert len(barrier_bare) == 1
        assert barrier_bare[0].qargs == (0, 1, 2, 3, 4)
        # The wide barrier connects cx(0,1) and cx(3,4) via shared qubits in
        # the barrier itself, so the otherwise-disjoint edges become ordered.
        assert instance.precedence_arcs() == frozenset({(0, 1)})

    def test_barrier_round_trip_preserves(self):
        qc = QuantumCircuit(2)
        qc.cx(0, 1)
        qc.barrier(0, 1)
        qc.cx(0, 1)
        instance, ctx = dag_to_instance(_to_dag(qc))
        # Two cx(0,1) in a row do not commute (arc 0->1) regardless of barrier.
        assert instance.precedence_arcs() == frozenset({(0, 1)})
        strat = Stratification(instance, [Layer(instance, [0]), Layer(instance, [1])])
        out_dag = stratification_to_dag(strat, ctx)
        names = [n.name for n in out_dag.topological_op_nodes()]
        assert names == ["box", "barrier", "box"]
        barrier_node = next(n for n in out_dag.topological_op_nodes() if n.name == "barrier")
        assert tuple(barrier_node.qargs) == tuple(ctx.qubits)

    def test_multiple_barriers_create_chain_of_arcs(self):
        qc = QuantumCircuit(2)
        qc.cz(0, 1)  # edge 0
        qc.barrier(0, 1)
        qc.cz(0, 1)  # edge 1
        qc.barrier(0, 1)
        qc.cz(0, 1)  # edge 2
        instance, _ = dag_to_instance(_to_dag(qc))
        # Hasse-reduced: 0 -> 1 -> 2 (transitive 0 -> 2 reduced away).
        assert instance.precedence_arcs() == frozenset({(0, 1), (1, 2)})

    def test_barrier_anchor_placement_pre_and_post(self):
        qc = QuantumCircuit(3)
        qc.barrier(0, 1, 2)  # before any edge
        qc.cx(0, 1)  # edge 0
        qc.barrier(0, 1, 2)  # after edge 0 on q0/q1; no edge yet on q2
        instance, ctx = dag_to_instance(_to_dag(qc))
        del instance
        barrier_anchors = [b.anchors for b in ctx.bare_ops if b.op.name == "barrier"]
        assert (None, None, None) in barrier_anchors
        assert (0, 0, None) in barrier_anchors


class TestEdgeFilter:
    """Tests for the ``edge_filter`` parameter of :func:`.dag_to_instance`."""

    def test_default_filter_excludes_meas_reset(self):
        """Default (gate_2q only): measure and reset stay as bare ops."""
        qc = QuantumCircuit(QuantumRegister(2, "q"), ClassicalRegister(1, "c"))
        qc.cx(0, 1)
        qc.measure(0, 0)
        qc.reset(1)
        instance, ctx = dag_to_instance(_to_dag(qc))
        assert instance.num_edges == 1  # only cx
        bare_names = [b.op.name for b in ctx.bare_ops]
        assert "measure" in bare_names
        assert "reset" in bare_names

    def test_measure_reset_filter_creates_1q_edges(self):
        """edge_filter={measure, reset}: meas/reset become 1-qubit edges."""
        qc = QuantumCircuit(QuantumRegister(2, "q"), ClassicalRegister(1, "c"))
        qc.cx(0, 1)
        qc.measure(0, 0)
        qc.reset(1)
        instance, ctx = dag_to_instance(_to_dag(qc), edge_filter={"measure", "reset"})
        # cx is now a bare op; measure and reset are edges
        assert instance.num_edges == 2
        edge_ops = [e.op.name for e in ctx.edge_ops]
        assert "measure" in edge_ops
        assert "reset" in edge_ops
        bare_names = [b.op.name for b in ctx.bare_ops]
        assert "cx" in bare_names

    def test_all_filter_creates_mixed_arity_edges(self):
        """edge_filter={gate_2q, measure, reset}: all three become edges."""
        qc = QuantumCircuit(QuantumRegister(2, "q"), ClassicalRegister(1, "c"))
        qc.cx(0, 1)
        qc.measure(0, 0)
        qc.reset(1)
        instance, ctx = dag_to_instance(_to_dag(qc), edge_filter={"gate_2q", "measure", "reset"})
        assert instance.num_edges == 3
        edge_names = {e.op.name for e in ctx.edge_ops}
        assert edge_names == {"cx", "measure", "reset"}

    def test_measure_edge_includes_cargs(self):
        """A measure edge records its classical bit index in cargs."""
        qc = QuantumCircuit(QuantumRegister(1, "q"), ClassicalRegister(1, "c"))
        qc.measure(0, 0)
        instance, ctx = dag_to_instance(_to_dag(qc), edge_filter={"measure"})
        assert instance.num_edges == 1
        eop = ctx.edge_ops[0]
        assert eop.op.name == "measure"
        assert eop.cargs == (0,)

    def test_reset_edge_has_empty_cargs(self):
        """A reset edge has no classical bits."""
        qc = QuantumCircuit(1)
        qc.reset(0)
        instance, ctx = dag_to_instance(_to_dag(qc), edge_filter={"reset"})
        assert instance.num_edges == 1
        eop = ctx.edge_ops[0]
        assert eop.op.name == "reset"
        assert eop.cargs == ()

    def test_meas_edge_round_trip_clbits(self):
        """Measure edges survive a dag_to_instance / stratification_to_dag round-trip."""
        qc = QuantumCircuit(QuantumRegister(1, "q"), ClassicalRegister(1, "c"))
        qc.measure(0, 0)
        dag = _to_dag(qc)
        instance, ctx = dag_to_instance(dag, edge_filter={"measure"})
        strat = Stratification(instance, [Layer(instance, [0])])
        out = stratification_to_dag(strat, ctx)
        box_nodes = [n for n in out.topological_op_nodes() if n.name == "box"]
        assert len(box_nodes) == 1
        body = box_nodes[0].op.body
        assert body.data[0].operation.name == "measure"
        assert len(body.clbits) == 1

    def test_no_meas_reset_in_circuit_all_modes_same(self):
        """A purely-unitary circuit is unaffected by any edge_filter value."""
        qc = QuantumCircuit(2)
        qc.cx(0, 1)
        dag = _to_dag(qc)
        inst_default, ctx_default = dag_to_instance(dag)
        inst_all, ctx_all = dag_to_instance(dag, edge_filter={"gate_2q", "measure", "reset"})
        assert inst_default.num_edges == inst_all.num_edges == 1
        strat_d = greedy_stratify(inst_default)
        strat_a = greedy_stratify(inst_all)
        out_d = _dag_op_names(stratification_to_dag(strat_d, ctx_default))
        out_a = _dag_op_names(stratification_to_dag(strat_a, ctx_all))
        assert out_d == out_a


class TestInputBoxOps:
    """Tests for how pre-existing BoxOps in the input DAG are handled."""

    def _make_dag_with_box(self):
        """Build a DAG containing a pre-existing BoxOp wrapping a CX gate."""
        inner = QuantumCircuit(2)
        inner.cx(0, 1)
        box = BoxOp(body=inner, annotations=[])
        qc = QuantumCircuit(4)
        qc.append(box, [0, 1])  # pre-existing box on qubits 0,1
        qc.cx(2, 3)  # a loose gate after the box
        return _to_dag(qc)

    def test_boxop_acts_as_barrier(self):
        """A BoxOp prevents reordering: gates before and after it get a precedence arc."""
        qc = QuantumCircuit(2)
        qc.cx(0, 1)
        inner = QuantumCircuit(2)
        inner.cx(0, 1)
        box = BoxOp(body=inner, annotations=[])
        qc.append(box, [0, 1])
        qc.cx(0, 1)
        dag = _to_dag(qc)
        instance, _ = dag_to_instance(dag)
        # Two loose CX gates (edges 0 and 1); the box is between them.
        assert instance.num_edges == 2
        # There must be a precedence arc (0 -> 1) even though cx commutes with cx.
        assert (0, 1) in instance.precedence_arcs()

    def test_boxop_pattern_in_external_patterns(self):
        """The box's content pattern is recorded in instance.external_patterns."""
        dag = self._make_dag_with_box()
        instance, _ = dag_to_instance(dag)
        # The box body contains cx(0,1). Its label should appear in external_patterns.
        assert len(instance.external_patterns) == 1

    def test_boxop_emitted_verbatim(self):
        """stratification_to_dag re-emits the original BoxOp unchanged."""
        dag = self._make_dag_with_box()
        instance, ctx = dag_to_instance(dag)
        strat = greedy_stratify(instance)
        out = stratification_to_dag(strat, ctx)
        names = _dag_op_names(out)
        # Exactly two boxes: the pre-existing one plus the new layer box.
        assert names.count("box") == 2

    def test_boxop_no_edges_still_reproduced(self):
        """A circuit with only a BoxOp and no loose gates round-trips cleanly."""
        inner = QuantumCircuit(2)
        inner.cx(0, 1)
        box = BoxOp(body=inner, annotations=[])
        qc = QuantumCircuit(2)
        qc.append(box, [0, 1])
        dag = _to_dag(qc)
        instance, ctx = dag_to_instance(dag)
        assert instance.num_edges == 0
        strat = Stratification(instance, [])
        out = stratification_to_dag(strat, ctx)
        names = _dag_op_names(out)
        assert names == ["box"]


class TestOrchestration:
    """Tests for :func:`.stratify_separate` and :func:`.stratify_mixed`."""

    @staticmethod
    def _meas_cx_circuit() -> "QuantumCircuit":
        """cx(0,1); measure(0); cx(2,3); measure(2)."""
        qc = QuantumCircuit(QuantumRegister(4, "q"), ClassicalRegister(2, "c"))
        qc.cx(0, 1)
        qc.measure(0, 0)
        qc.cx(2, 3)
        qc.measure(2, 1)
        return qc

    def test_stratify_mixed_all_ops_in_boxes(self):
        """stratify_mixed places all ops (gates + meas) inside boxes."""
        dag = _to_dag(self._meas_cx_circuit())
        out = stratify_mixed(dag, greedy_stratify)
        names = _dag_op_names(out)
        assert "measure" not in names
        assert "cx" not in names
        for contents in _box_contents(out):
            assert len(contents) > 0

    def test_stratify_mixed_depth_le_separate(self):
        """Mixed mode depth ≤ separate mode depth (joint optimisation is at least as good)."""
        dag = _to_dag(self._meas_cx_circuit())
        out_mixed = stratify_mixed(dag, greedy_stratify)
        out_sep = stratify_separate(dag, greedy_stratify)
        depth_mixed = _dag_op_names(out_mixed).count("box")
        depth_sep = _dag_op_names(out_sep).count("box")
        assert depth_mixed <= depth_sep

    def test_stratify_separate_boxes_are_kind_homogeneous(self):
        """In separate mode every box is either all-gate or all-meas/reset."""
        dag = _to_dag(self._meas_cx_circuit())
        out = stratify_separate(dag, greedy_stratify)
        for contents in _box_contents(out):
            has_gate = any(n not in ("measure", "reset") for n in contents)
            has_mr = any(n in ("measure", "reset") for n in contents)
            # A box may contain only gates OR only meas/reset, never both.
            assert not (has_gate and has_mr)

    def test_stratify_separate_better_than_post_hoc(self):
        """For the classic 4-op circuit the two-pass result has ≤ 3 boxes.

        Post-hoc boxing would produce 4 (gate box 0, mr box 0, gate box 1, mr box 1).
        Joint scheduling should merge both measure ops into one layer → ≤ 3.
        """
        dag = _to_dag(self._meas_cx_circuit())
        out = stratify_separate(dag, greedy_stratify)
        num_boxes = _dag_op_names(out).count("box")
        assert num_boxes <= 3

    def test_stratify_separate_respects_existing_boxes(self):
        """Pass-2 leaves pass-1 boxes intact and counts their patterns."""
        # Run pass 1 manually (meas/reset only) to get a dag with meas boxes.
        inst1, ctx1 = dag_to_instance(_to_dag(self._meas_cx_circuit()), edge_filter={"measure"})
        strat1 = greedy_stratify(inst1)
        dag1 = stratification_to_dag(strat1, ctx1)

        # Pass 2 should see the meas boxes as barriers and count their patterns.
        inst2, ctx2 = dag_to_instance(dag1, edge_filter={"gate_2q"})
        assert len(inst2.external_patterns) > 0  # box patterns were captured
        assert len(ctx2.boxes) > 0  # boxes were recorded in context

        strat2 = greedy_stratify(inst2)
        out = stratification_to_dag(strat2, ctx2)
        # Both gate boxes and original meas boxes should appear.
        names = _dag_op_names(out)
        assert names.count("box") >= 2

    def test_stratify_mixed_no_meas_same_as_default(self):
        """For a purely-unitary circuit, stratify_mixed gives the same result as default."""
        qc = QuantumCircuit(4)
        qc.cx(0, 1)
        qc.cx(2, 3)
        dag = _to_dag(qc)
        out_mixed = stratify_mixed(dag, greedy_stratify)
        inst_default, ctx_default = dag_to_instance(dag)
        out_default = stratification_to_dag(greedy_stratify(inst_default), ctx_default)
        assert _dag_op_names(out_mixed) == _dag_op_names(out_default)

    def test_stratify_separate_meas_first_vs_gates_first(self):
        """Both orderings of stratify_separate produce valid results."""
        dag = _to_dag(self._meas_cx_circuit())
        out_mf = stratify_separate(dag, greedy_stratify, meas_first=True)
        out_gf = stratify_separate(dag, greedy_stratify, meas_first=False)
        # Both must have only boxes at the top level.
        for n in out_mf.topological_op_nodes():
            assert n.name == "box"
        for n in out_gf.topological_op_nodes():
            assert n.name == "box"
