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

"""Unit tests for the stratification IR classes."""

import pytest

from samplomatic.stratification import Hypergraph, Layer, Stratification, StratificationInstance

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_simple_instance(labels=None):
    """Return a small StratificationInstance for shared use.

    Edges:
        0: {0, 1}
        1: {2, 3}
        2: {0, 2}   (conflicts with 0 and 1)

    Precedence: 0 ≺ 2  (so edge 0 must come before edge 2)
    Labels: ("cx", "cx", "cz") if not overridden.
    """
    hyp = Hypergraph(4, [{0, 1}, {2, 3}, {0, 2}])
    if labels is None:
        labels = ["cx", "cx", "cz"]
    return StratificationInstance(hyp, [(0, 2)], labels)


# ---------------------------------------------------------------------------
# Hypergraph
# ---------------------------------------------------------------------------


class TestHypergraph:
    """Tests for the Hypergraph class."""

    def test_basic_construction(self):
        """Construct a valid 2-uniform hypergraph."""
        h = Hypergraph(4, [{0, 1}, {2, 3}, {1, 2}])
        assert h.num_vertices == 4
        assert h.num_edges == 3
        assert h.edges == (frozenset({0, 1}), frozenset({2, 3}), frozenset({1, 2}))

    def test_vertices_property(self):
        """vertices is range(num_vertices)."""
        h = Hypergraph(5, [{0, 1}])
        assert list(h.vertices) == [0, 1, 2, 3, 4]

    def test_len(self):
        """__len__ returns num_edges."""
        h = Hypergraph(3, [{0, 1}, {1, 2}])
        assert len(h) == 2

    def test_negative_num_vertices_raises(self):
        """Negative num_vertices raises ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            Hypergraph(-1, [])

    def test_empty_edge_raises(self):
        """An empty edge raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            Hypergraph(3, [[], {0, 1}])

    def test_out_of_range_vertex_raises(self):
        """A vertex index outside range raises ValueError."""
        with pytest.raises(ValueError, match="outside"):
            Hypergraph(3, [{0, 5}])

    def test_multiset_edges(self):
        """Repeated edges are allowed (multiset semantics)."""
        h = Hypergraph(2, [{0, 1}, {0, 1}])
        assert h.num_edges == 2

    def test_incident(self):
        """incident(v) returns the correct edge IDs."""
        h = Hypergraph(4, [{0, 1}, {2, 3}, {1, 2}])
        assert set(h.incident(1)) == {0, 2}
        assert set(h.incident(3)) == {1}
        assert set(h.incident(0)) == {0}

    def test_conflict(self):
        """conflict(e, e') is True iff the edges share a vertex."""
        h = Hypergraph(4, [{0, 1}, {2, 3}, {1, 2}])
        assert not h.conflict(0, 1)
        assert h.conflict(0, 2)
        assert h.conflict(1, 2)

    def test_is_strong_matching_true(self):
        """Disjoint edges form a strong matching."""
        h = Hypergraph(4, [{0, 1}, {2, 3}])
        assert h.is_strong_matching([0, 1])

    def test_is_strong_matching_false(self):
        """Overlapping edges do not form a strong matching."""
        h = Hypergraph(4, [{0, 1}, {1, 2}])
        assert not h.is_strong_matching([0, 1])

    def test_equality_and_hash(self):
        """Equal hypergraphs have equal hashes."""
        h1 = Hypergraph(3, [{0, 1}, {1, 2}])
        h2 = Hypergraph(3, [{0, 1}, {1, 2}])
        h3 = Hypergraph(3, [{1, 2}, {0, 1}])  # different edge order
        assert h1 == h2
        assert hash(h1) == hash(h2)
        assert h1 != h3  # order matters (multiset by index)

    def test_not_equal_different_num_vertices(self):
        """Hypergraphs with different num_vertices are not equal."""
        h1 = Hypergraph(3, [{0, 1}])
        h2 = Hypergraph(4, [{0, 1}])
        assert h1 != h2


# ---------------------------------------------------------------------------
# StratificationInstance
# ---------------------------------------------------------------------------


class TestStratificationInstance:
    """Tests for the StratificationInstance class."""

    def test_basic_construction(self):
        """Construct a valid instance from arc pairs."""
        inst = make_simple_instance()
        assert inst.num_vertices == 4
        assert inst.num_edges == 3
        assert set(inst.labels) == {"cx", "cz"}
        assert inst.alphabet == {"cx", "cz"}

    def test_label_count_mismatch_raises(self):
        """Mismatched label count raises ValueError."""
        hyp = Hypergraph(4, [{0, 1}, {2, 3}])
        with pytest.raises(ValueError, match="2 labels"):
            StratificationInstance(hyp, [], ["a"])

    def test_cycle_raises(self):
        """A cycle in the precedence relation raises ValueError."""
        hyp = Hypergraph(4, [{0, 1}, {2, 3}])
        with pytest.raises(ValueError, match="cycle"):
            StratificationInstance(hyp, [(0, 1), (1, 0)], ["a", "b"])

    def test_predecessors_chain(self):
        """predecessors follows transitive closure on a chain 0 ≺ 1 ≺ 2."""
        hyp = Hypergraph(6, [{0, 1}, {2, 3}, {4, 5}])
        inst = StratificationInstance(hyp, [(0, 1), (1, 2)], ["a", "b", "c"])
        assert inst.predecessors(2) == {0, 1}
        assert inst.predecessors(1) == {0}
        assert inst.predecessors(0) == frozenset()

    def test_successors_chain(self):
        """successors follows transitive closure."""
        hyp = Hypergraph(6, [{0, 1}, {2, 3}, {4, 5}])
        inst = StratificationInstance(hyp, [(0, 1), (1, 2)], ["a", "b", "c"])
        assert inst.successors(0) == {1, 2}

    def test_immediate_predecessors(self):
        """immediate_predecessors returns only direct Hasse-diagram predecessors."""
        hyp = Hypergraph(6, [{0, 1}, {2, 3}, {4, 5}])
        # Even if we supply the transitive arc (0,2), Hasse reduction removes it.
        inst2 = StratificationInstance(hyp, [(0, 1), (1, 2), (0, 2)], ["a", "b", "c"])
        assert inst2.immediate_predecessors(2) == {1}

    def test_is_comparable(self):
        """is_comparable is True for edges in a precedence relation."""
        inst = make_simple_instance()
        assert inst.is_comparable(0, 2)
        assert not inst.is_comparable(0, 1)

    def test_chain_height_chain(self):
        """chain_height on a chain 0 ≺ 1 ≺ 2."""
        hyp = Hypergraph(6, [{0, 1}, {2, 3}, {4, 5}])
        inst = StratificationInstance(hyp, [(0, 1), (1, 2)], ["a", "b", "c"])
        assert inst.chain_height(0) == 2
        assert inst.chain_height(1) == 1
        assert inst.chain_height(2) == 0

    def test_chain_height_antichain(self):
        """All chain heights are 0 when there are no precedence arcs."""
        hyp = Hypergraph(4, [{0, 1}, {2, 3}])
        inst = StratificationInstance(hyp, [], ["a", "b"])
        assert inst.chain_height(0) == 0
        assert inst.chain_height(1) == 0

    def test_chain_height_diamond(self):
        """chain_height on a diamond: 0 ≺ {1, 2} ≺ 3."""
        hyp = Hypergraph(8, [{0, 1}, {2, 3}, {4, 5}, {6, 7}])
        inst = StratificationInstance(hyp, [(0, 1), (0, 2), (1, 3), (2, 3)], ["a"] * 4)
        assert inst.chain_height(0) == 2
        assert inst.chain_height(1) == 1
        assert inst.chain_height(2) == 1
        assert inst.chain_height(3) == 0

    def test_linear_extension_respects_order(self):
        """linear_extension returns a topological sort."""
        inst = make_simple_instance()
        ext = inst.linear_extension()
        assert ext.index(0) < ext.index(2)

    def test_is_antichain_true(self):
        """Incomparable edges form an antichain."""
        inst = make_simple_instance()
        assert inst.is_antichain([0, 1])

    def test_is_antichain_false(self):
        """Comparable edges do not form an antichain."""
        inst = make_simple_instance()
        assert not inst.is_antichain([0, 2])

    def test_is_layer_true(self):
        """Disjoint incomparable edges form a valid layer."""
        inst = make_simple_instance()
        assert inst.is_layer([0, 1])  # edges {0,1} and {2,3} are disjoint and incomparable

    def test_is_layer_false_conflict(self):
        """Conflicting edges (shared vertex) are not a valid layer."""
        inst = make_simple_instance()
        assert not inst.is_layer([1, 2])  # share vertex 2

    def test_is_layer_false_comparable(self):
        """Comparable edges are not a valid layer."""
        inst = make_simple_instance()
        assert not inst.is_layer([0, 2])

    def test_pattern_of(self):
        """pattern_of returns the correct label set."""
        inst = make_simple_instance()
        assert inst.pattern_of([0, 1]) == frozenset({"cx"})
        assert inst.pattern_of([1, 2]) == frozenset({"cx", "cz"})

    def test_vertices_of(self):
        """vertices_of returns the union of vertex sets."""
        inst = make_simple_instance()
        assert inst.vertices_of([0, 1]) == frozenset({0, 1, 2, 3})

    def test_equality_and_hash(self):
        """Equal instances have equal hashes."""
        inst1 = make_simple_instance()
        inst2 = make_simple_instance()
        assert inst1 == inst2
        assert hash(inst1) == hash(inst2)

    def test_hasse_reduction(self):
        """Supplying redundant transitive arcs is equivalent to the Hasse diagram."""
        hyp = Hypergraph(6, [{0, 1}, {2, 3}, {4, 5}])
        inst_minimal = StratificationInstance(hyp, [(0, 1), (1, 2)], ["a", "b", "c"])
        inst_full = StratificationInstance(hyp, [(0, 1), (1, 2), (0, 2)], ["a", "b", "c"])
        assert inst_minimal == inst_full


# ---------------------------------------------------------------------------
# Layer
# ---------------------------------------------------------------------------


class TestLayer:
    """Tests for the Layer class."""

    def test_basic_construction(self):
        """Construct a valid layer."""
        inst = make_simple_instance()
        layer = Layer(inst, [0, 1])
        assert layer.edges == frozenset({0, 1})

    def test_pattern(self):
        """Layer.pattern returns the correct frozenset of labels."""
        inst = make_simple_instance()
        layer = Layer(inst, [0, 1])
        assert layer.pattern == frozenset({"cx"})

    def test_vertices(self):
        """Layer.vertices returns the union of edge vertex sets."""
        inst = make_simple_instance()
        layer = Layer(inst, [0, 1])
        assert layer.vertices == frozenset({0, 1, 2, 3})

    def test_comparable_edges_raise(self):
        """Edges that are comparable in ≺ raise ValueError."""
        inst = make_simple_instance()
        with pytest.raises(ValueError, match="antichain"):
            Layer(inst, [0, 2])

    def test_conflicting_edges_raise(self):
        """Edges sharing a vertex raise ValueError."""
        inst = make_simple_instance()
        with pytest.raises(ValueError, match="matching"):
            Layer(inst, [1, 2])

    def test_len(self):
        """__len__ returns the number of edges in the layer."""
        inst = make_simple_instance()
        layer = Layer(inst, [0, 1])
        assert len(layer) == 2

    def test_iter_and_contains(self):
        """__iter__ and __contains__ work on edge IDs."""
        inst = make_simple_instance()
        layer = Layer(inst, [0, 1])
        assert 0 in layer
        assert 2 not in layer
        assert set(layer) == {0, 1}

    def test_equality(self):
        """Equal layers compare as equal."""
        inst = make_simple_instance()
        l1 = Layer(inst, [0, 1])
        l2 = Layer(inst, [1, 0])  # same edges, different order
        assert l1 == l2
        assert hash(l1) == hash(l2)

    def test_inequality_different_edges(self):
        """Layers with different edges are not equal."""
        inst = make_simple_instance()
        l1 = Layer(inst, [0, 1])
        l2 = Layer(inst, [2])  # only edge 2 (which is a valid single-edge layer)
        assert l1 != l2

    def test_single_edge_layer(self):
        """A layer with a single edge is always valid."""
        inst = make_simple_instance()
        for eid in range(inst.num_edges):
            layer = Layer(inst, [eid])
            assert eid in layer


# ---------------------------------------------------------------------------
# Stratification
# ---------------------------------------------------------------------------


class TestStratification:
    """Tests for the Stratification class."""

    def _make_stratification(self):
        """Return a valid stratification of make_simple_instance.

        Layers:
            L0: {0, 1}  — edges {0,1} and {2,3}, incomparable, disjoint
            L1: {2}     — edge {0,2}, after edge 0 (satisfied since 0 ≺ 2)
        """
        inst = make_simple_instance()
        l0 = Layer(inst, [0, 1])
        l1 = Layer(inst, [2])
        return Stratification(inst, [l0, l1]), inst

    def test_basic_construction(self):
        """Construct a valid stratification."""
        strat, inst = self._make_stratification()
        assert strat.depth == 2
        assert strat.unique_pattern_count == 2  # {"cx"} and {"cz"}

    def test_depth_and_unique_pattern_count(self):
        """depth and unique_pattern_count are correct."""
        inst = make_simple_instance(labels=["cx", "cx", "cx"])
        l0 = Layer(inst, [0, 1])
        l1 = Layer(inst, [2])
        strat = Stratification(inst, [l0, l1])
        assert strat.depth == 2
        assert strat.unique_pattern_count == 1  # both layers have pattern {"cx"}

    def test_patterns(self):
        """patterns returns the correct frozenset of frozensets."""
        strat, _ = self._make_stratification()
        assert strat.patterns == frozenset({frozenset({"cx"}), frozenset({"cz"})})

    def test_key_depth_first(self):
        """key_depth_first is (depth, unique_pattern_count)."""
        strat, _ = self._make_stratification()
        assert strat.key_depth_first == (2, 2)

    def test_key_pattern_first(self):
        """key_pattern_first is (unique_pattern_count, depth)."""
        strat, _ = self._make_stratification()
        assert strat.key_pattern_first == (2, 2)

    def test_len_and_iter(self):
        """__len__ and __iter__ work over layers."""
        strat, _ = self._make_stratification()
        assert len(strat) == 2
        layers = list(strat)
        assert len(layers) == 2

    def test_getitem(self):
        """__getitem__ returns the correct layer."""
        strat, inst = self._make_stratification()
        assert strat[0].edges == frozenset({0, 1})
        assert strat[1].edges == frozenset({2})

    def test_missing_edges_raise(self):
        """A stratification that does not cover all edges raises ValueError."""
        inst = make_simple_instance()
        l0 = Layer(inst, [0, 1])
        with pytest.raises(ValueError, match="Missing"):
            Stratification(inst, [l0])

    def test_duplicate_edges_raise(self):
        """A stratification with an edge in two layers raises ValueError."""
        inst = make_simple_instance()
        l0 = Layer(inst, [0])
        l1 = Layer(inst, [0, 1])
        l2 = Layer(inst, [2])
        with pytest.raises(ValueError, match="appears in both"):
            Stratification(inst, [l0, l1, l2])

    def test_precedence_violation_raises(self):
        """Swapping layers that violate ≺ raises ValueError."""
        inst = make_simple_instance()
        l0 = Layer(inst, [2])
        l1 = Layer(inst, [0, 1])
        with pytest.raises(ValueError, match="Precedence"):
            Stratification(inst, [l0, l1])

    def test_wrong_instance_raises(self):
        """A layer from a different instance raises ValueError."""
        inst1 = make_simple_instance()
        inst2 = make_simple_instance()  # equal value, different object
        l0 = Layer(inst1, [0, 1])
        l1 = Layer(inst2, [2])
        with pytest.raises(ValueError, match="different StratificationInstance"):
            Stratification(inst1, [l0, l1])

    def test_equality(self):
        """Equal stratifications compare as equal."""
        strat1, _ = self._make_stratification()
        strat2, _ = self._make_stratification()
        # Different instance objects but same value — identity check means != here.
        assert strat1 != strat2  # different instance objects

    def test_equality_same_instance(self):
        """Two stratifications built from the same instance object are equal."""
        inst = make_simple_instance()
        l0a = Layer(inst, [0, 1])
        l1a = Layer(inst, [2])
        l0b = Layer(inst, [0, 1])
        l1b = Layer(inst, [2])
        s1 = Stratification(inst, [l0a, l1a])
        s2 = Stratification(inst, [l0b, l1b])
        assert s1 == s2
        assert hash(s1) == hash(s2)

    def test_external_patterns_count(self):
        """external_patterns are included in unique_pattern_count."""
        # Instance with one external pattern distinct from the layer patterns.
        external = frozenset({"ecr"})
        hyp = Hypergraph(4, [{0, 1}, {2, 3}, {0, 2}])
        inst = StratificationInstance(
            hyp, [(0, 2)], ["cx", "cx", "cz"], external_patterns=[external]
        )
        l0 = Layer(inst, [0, 1])
        l1 = Layer(inst, [2])
        strat = Stratification(inst, [l0, l1])
        # Layer patterns: {cx}, {cz}. External: {ecr}. Total unique = 3.
        assert strat.unique_pattern_count == 3
        assert external in strat.patterns

    def test_external_patterns_no_double_count(self):
        """If an external pattern matches a layer pattern it is not double-counted."""
        external = frozenset({"cx"})  # same as both layers' patterns
        hyp = Hypergraph(4, [{0, 1}, {2, 3}, {0, 2}])
        inst = StratificationInstance(
            hyp, [(0, 2)], ["cx", "cx", "cx"], external_patterns=[external]
        )
        l0 = Layer(inst, [0, 1])
        l1 = Layer(inst, [2])
        strat = Stratification(inst, [l0, l1])
        # Layer patterns: {cx}. External: {cx}. Union has size 1.
        assert strat.unique_pattern_count == 1

    def test_no_external_patterns_default(self):
        """Without external_patterns the count is unchanged from the original behaviour."""
        strat, _ = self._make_stratification()
        assert strat.unique_pattern_count == 2  # {cx}, {cz}
