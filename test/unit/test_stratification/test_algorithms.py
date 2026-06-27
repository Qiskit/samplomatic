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

"""Unit tests for the stratification scheduling algorithms."""

import pytest
from qiskit.converters import circuit_to_dag

from samplomatic.stratification import (
    Hypergraph,
    Layer,
    Stratification,
    StratificationInstance,
    coffman_graham_stratify,
    dag_to_instance,
    grasp_stratify,
    greedy_stratify,
    ilp_stratify,
    pattern_batch_stratify,
    refine_stratification,
)
from samplomatic.stratification._circuit_families import ALL_FAMILIES, build

# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------


def make_chain_instance(n: int) -> StratificationInstance:
    """n non-conflicting 2-edges in a chain 0 ≺ 1 ≺ ... ≺ n-1, all label 'cx'.

    Edges use disjoint pairs: edge i uses vertices {2i, 2i+1}.
    Optimal: depth = n, unique_pattern_count = 1.
    """
    edges = [{2 * i, 2 * i + 1} for i in range(n)]
    hyp = Hypergraph(2 * n, edges)
    arcs = [(i, i + 1) for i in range(n - 1)]
    return StratificationInstance(hyp, arcs, ["cx"] * n)


def make_simple_instance() -> StratificationInstance:
    """4 vertices, 3 edges: {0,1}, {2,3}, {0,2}. Arc: 0 ≺ 2. Labels: cx,cx,cz."""
    hyp = Hypergraph(4, [{0, 1}, {2, 3}, {0, 2}])
    return StratificationInstance(hyp, [(0, 2)], ["cx", "cx", "cz"])


def make_two_pattern_instance() -> StratificationInstance:
    """4 vertices, 4 edges, labels a/b/a/b with no precedence arcs."""
    hyp = Hypergraph(4, [{0, 1}, {2, 3}, {0, 2}, {1, 3}])
    return StratificationInstance(hyp, [], ["a", "b", "a", "b"])


def make_diamond_instance() -> StratificationInstance:
    """Diamond-shaped precedence: edges 0,1 ≺ 2,3 (0≺2, 0≺3, 1≺2, 1≺3).

    Edges: 0:{0,1}(cx), 1:{2,3}(cx), 2:{4,5}(cx), 3:{6,7}(cx).
    Non-conflicting (disjoint vertex sets).
    Optimal: depth=2, unique_pattern_count=1.
    """
    hyp = Hypergraph(8, [{0, 1}, {2, 3}, {4, 5}, {6, 7}])
    arcs = [(0, 2), (0, 3), (1, 2), (1, 3)]
    return StratificationInstance(hyp, arcs, ["cx", "cx", "cx", "cx"])


def _validate_stratification(strat: Stratification, instance: StratificationInstance) -> None:
    """Assert that strat is valid and covers all edges of instance."""
    assert strat.instance is instance
    edge_set = set()
    for layer in strat.layers:
        for e in layer.edges:
            assert e not in edge_set, f"Duplicate edge {e}"
            edge_set.add(e)
    assert edge_set == set(range(instance.num_edges)), "Not all edges covered"
    assert strat.depth >= 0
    assert strat.unique_pattern_count >= 0


# ---------------------------------------------------------------------------
# TestGreedyStratify
# ---------------------------------------------------------------------------


class TestGreedyStratify:
    def test_returns_stratification(self):
        s = greedy_stratify(make_simple_instance())
        assert isinstance(s, Stratification)

    def test_covers_all_edges(self):
        inst = make_simple_instance()
        _validate_stratification(greedy_stratify(inst), inst)

    def test_empty_instance(self):
        hyp = Hypergraph(4, [])
        inst = StratificationInstance(hyp, [], [])
        s = greedy_stratify(inst)
        assert s.depth == 0

    def test_chain_depth_equals_chain_length(self):
        inst = make_chain_instance(5)
        s = greedy_stratify(inst)
        assert s.depth == 5
        assert s.unique_pattern_count == 1

    def test_simple_instance_layout(self):
        """Edges 0 and 1 are non-conflicting and independent -> same layer.

        Edge 2 conflicts with both and must come after edge 0.
        """
        inst = make_simple_instance()
        s = greedy_stratify(inst)
        assert s.depth == 2
        assert s.layers[0].edges == frozenset({0, 1})
        assert s.layers[1].edges == frozenset({2})

    def test_precedence_respected(self):
        inst = make_diamond_instance()
        s = greedy_stratify(inst)
        depth_of = {e: k for k, layer in enumerate(s.layers) for e in layer.edges}
        assert depth_of[0] < depth_of[2]
        assert depth_of[0] < depth_of[3]
        assert depth_of[1] < depth_of[2]
        assert depth_of[1] < depth_of[3]


# ---------------------------------------------------------------------------
# TestCoffmanGrahamStratify
# ---------------------------------------------------------------------------


class TestCoffmanGrahamStratify:
    def test_returns_stratification(self):
        assert isinstance(coffman_graham_stratify(make_simple_instance()), Stratification)

    def test_covers_all_edges(self):
        inst = make_simple_instance()
        _validate_stratification(coffman_graham_stratify(inst), inst)

    def test_empty_instance(self):
        hyp = Hypergraph(2, [])
        inst = StratificationInstance(hyp, [], [])
        assert coffman_graham_stratify(inst).depth == 0

    def test_chain_depth_optimal(self):
        inst = make_chain_instance(4)
        s = coffman_graham_stratify(inst)
        assert s.depth == 4

    def test_chain_height_priority(self):
        """On a linear chain 0≺1≺2, B picks 0 first (highest chain_height=2)."""
        hyp = Hypergraph(6, [{0, 1}, {2, 3}, {4, 5}])
        inst = StratificationInstance(hyp, [(0, 1), (1, 2)], ["a", "b", "c"])
        s = coffman_graham_stratify(inst)
        assert s.depth == 3
        depth_of = {e: k for k, layer in enumerate(s.layers) for e in layer.edges}
        assert depth_of[0] < depth_of[1] < depth_of[2]

    def test_precedence_respected(self):
        inst = make_diamond_instance()
        s = coffman_graham_stratify(inst)
        depth_of = {e: k for k, layer in enumerate(s.layers) for e in layer.edges}
        for e_pred, e_succ in inst.precedence_arcs():
            assert depth_of[e_pred] < depth_of[e_succ]


# ---------------------------------------------------------------------------
# TestPatternBatchStratify
# ---------------------------------------------------------------------------


class TestPatternBatchStratify:
    def test_returns_stratification(self):
        assert isinstance(pattern_batch_stratify(make_simple_instance()), Stratification)

    def test_covers_all_edges(self):
        inst = make_simple_instance()
        _validate_stratification(pattern_batch_stratify(inst), inst)

    def test_empty_instance(self):
        hyp = Hypergraph(2, [])
        inst = StratificationInstance(hyp, [], [])
        assert pattern_batch_stratify(inst).depth == 0

    def test_layers_are_monochromatic(self):
        for inst in [make_simple_instance(), make_chain_instance(3), make_diamond_instance()]:
            s = pattern_batch_stratify(inst)
            for layer in s.layers:
                assert len(layer.pattern) == 1, f"Non-monochromatic: {layer.pattern}"

    def test_pattern_bound(self):
        for inst in [make_simple_instance(), make_chain_instance(4)]:
            s = pattern_batch_stratify(inst)
            assert s.unique_pattern_count <= len(inst.alphabet)

    def test_larger_matching_preferred(self):
        """Label with a 3-way matching beats label with a 1-way matching."""
        hyp = Hypergraph(8, [{0, 1}, {2, 3}, {4, 5}, {6, 7}])
        inst = StratificationInstance(hyp, [], ["a", "a", "a", "b"])
        s = pattern_batch_stratify(inst)
        assert s.layers[0].pattern == frozenset({"a"})
        assert len(s.layers[0].edges) == 3


# ---------------------------------------------------------------------------
# TestIlpStratify
# ---------------------------------------------------------------------------


class TestIlpStratify:
    def test_returns_stratification(self):
        pytest.importorskip("pulp")
        inst = make_simple_instance()
        s = ilp_stratify(inst)
        assert isinstance(s, Stratification)

    def test_covers_all_edges(self):
        pytest.importorskip("pulp")
        inst = make_simple_instance()
        _validate_stratification(ilp_stratify(inst), inst)

    def test_empty_instance(self):
        pytest.importorskip("pulp")
        hyp = Hypergraph(2, [])
        inst = StratificationInstance(hyp, [], [])
        assert ilp_stratify(inst).depth == 0

    def test_depth_optimal_on_simple_instance(self):
        """The simple instance has known optimal depth 2."""
        pytest.importorskip("pulp")
        inst = make_simple_instance()
        s = ilp_stratify(inst, objective="depth")
        assert s.depth == 2

    def test_beats_or_matches_greedy(self):
        """ILP (exact) depth must be <= greedy's depth."""
        pytest.importorskip("pulp")
        inst = make_simple_instance()
        assert ilp_stratify(inst, objective="depth").depth <= greedy_stratify(inst).depth

    def test_pattern_objective_runs(self):
        """objective='pattern' returns a valid stratification."""
        pytest.importorskip("pulp")
        inst = make_simple_instance()
        s = ilp_stratify(inst, objective="pattern")
        assert isinstance(s, Stratification)
        _validate_stratification(s, inst)

    def test_time_limit_returns_valid(self):
        """A time limit still returns a valid stratification (greedy fallback if needed)."""
        pytest.importorskip("pulp")
        inst = make_simple_instance()
        s = ilp_stratify(inst, time_limit=0.1)
        _validate_stratification(s, inst)


# ---------------------------------------------------------------------------
# TestGraspStratify
# ---------------------------------------------------------------------------


class TestGraspStratify:
    def test_returns_stratification(self):
        inst = make_simple_instance()
        s = grasp_stratify(inst, restarts=3, seed=0)
        assert isinstance(s, Stratification)

    def test_covers_all_edges(self):
        inst = make_simple_instance()
        _validate_stratification(grasp_stratify(inst, restarts=3, seed=0), inst)

    def test_empty_instance(self):
        hyp = Hypergraph(2, [])
        inst = StratificationInstance(hyp, [], [])
        assert grasp_stratify(inst, restarts=3, seed=0).depth == 0

    def test_seeded_reproducible(self):
        inst = make_simple_instance()
        s1 = grasp_stratify(inst, restarts=5, seed=42)
        s2 = grasp_stratify(inst, restarts=5, seed=42)
        assert s1 == s2

    def test_alpha_zero_deterministic_across_seeds(self):
        """alpha=0 => fully greedy => same result regardless of seed."""
        inst = make_chain_instance(4)
        s1 = grasp_stratify(inst, base="greedy", alpha=0, restarts=3, seed=1)
        s2 = grasp_stratify(inst, base="greedy", alpha=0, restarts=3, seed=99)
        assert s1.key_depth_first == s2.key_depth_first

    def test_each_base_works(self):
        inst = make_simple_instance()
        for base in ("greedy", "coffman_graham"):
            s = grasp_stratify(inst, base=base, restarts=3, seed=0)
            _validate_stratification(s, inst)

    def test_invalid_base_raises(self):
        inst = make_simple_instance()
        with pytest.raises(ValueError, match="Unknown base"):
            grasp_stratify(inst, base="invalid_algorithm")

    def test_key_pattern_first(self):
        inst = make_simple_instance()
        s = grasp_stratify(inst, key="pattern", restarts=5, seed=0)
        assert isinstance(s, Stratification)
        _validate_stratification(s, inst)


# ---------------------------------------------------------------------------
# TestRefineStratification
# ---------------------------------------------------------------------------


class TestRefineStratification:
    def test_returns_stratification(self):
        inst = make_simple_instance()
        s = greedy_stratify(inst)
        r = refine_stratification(s)
        assert isinstance(r, Stratification)

    def test_covers_all_edges(self):
        inst = make_simple_instance()
        s = greedy_stratify(inst)
        _validate_stratification(refine_stratification(s), inst)

    def test_empty_instance(self):
        hyp = Hypergraph(2, [])
        inst = StratificationInstance(hyp, [], [])
        s = greedy_stratify(inst)
        assert refine_stratification(s).depth == 0

    def test_never_worsens_depth_first(self):
        for inst in [make_simple_instance(), make_chain_instance(3), make_diamond_instance()]:
            s = greedy_stratify(inst)
            r = refine_stratification(s, key="depth")
            assert r.key_depth_first <= s.key_depth_first

    def test_never_worsens_pattern_first(self):
        for inst in [make_simple_instance(), make_chain_instance(3)]:
            s = greedy_stratify(inst)
            r = refine_stratification(s, key="pattern")
            assert r.key_pattern_first <= s.key_pattern_first

    def test_swap_preserves_strong_matching(self):
        """Swap move must not corrupt the strong-matching invariant.

        Construct an instance where two edges share a vertex and can be swapped
        within their slack windows.  The old code corrupted layer_verts when
        simulating such a swap via two sequential _relocate_edge calls.
        """
        # Edges: 0:{0,1}, 1:{1,2}, 2:{2,3} — each pair shares a vertex.
        # Arcs: 0 < 2 (so edge 0 must come before edge 2).
        hyp = Hypergraph(4, [{0, 1}, {1, 2}, {2, 3}])
        inst = StratificationInstance(hyp, [(0, 2)], ["cx", "cx", "cx"])
        s = greedy_stratify(inst)
        r = refine_stratification(s, key="depth")
        _validate_stratification(r, inst)

    def test_merge_reduces_depth(self):
        """Two compatible independent edges placed in separate layers get merged to one."""
        hyp = Hypergraph(4, [{0, 1}, {2, 3}])
        inst = StratificationInstance(hyp, [], ["cx", "cx"])
        layer0 = Layer(inst, [0])
        layer1 = Layer(inst, [1])
        s = Stratification(inst, [layer0, layer1])
        assert s.depth == 2
        r = refine_stratification(s, key="depth")
        assert r.depth == 1

    def test_original_unchanged(self):
        """The input stratification object is not mutated."""
        inst = make_simple_instance()
        s = greedy_stratify(inst)
        original_depth = s.depth
        original_layers = s.layers
        refine_stratification(s, key="depth")
        assert s.depth == original_depth
        assert s.layers == original_layers

    def test_idempotent(self):
        """refine(refine(s)) should have the same key as refine(s)."""
        inst = make_simple_instance()
        s = greedy_stratify(inst)
        r1 = refine_stratification(s, key="depth")
        r2 = refine_stratification(r1, key="depth")
        assert r2.key_depth_first == r1.key_depth_first


# ---------------------------------------------------------------------------
# TestCircuitFamiliesSmoke
# ---------------------------------------------------------------------------


class TestCircuitFamiliesSmoke:
    """Smoke tests running all algorithms on all 14 circuit families."""

    def test_all_algorithms_on_all_families(self):
        """Every algorithm returns a valid Stratification on every benchmark circuit."""
        _pulp_available = True
        try:
            import pulp  # noqa: F401
        except ImportError:
            _pulp_available = False

        all_algos = {
            "greedy": greedy_stratify,
            "coffman_graham": coffman_graham_stratify,
            "pattern_batch": pattern_batch_stratify,
            "grasp": lambda inst: grasp_stratify(inst, restarts=3, seed=0),
            "refine": lambda inst: refine_stratification(greedy_stratify(inst)),
        }
        if _pulp_available:
            all_algos["ilp"] = lambda inst: ilp_stratify(inst, time_limit=10.0)

        errors = []
        for family in ALL_FAMILIES:
            qc = build(family)
            inst, _ = dag_to_instance(circuit_to_dag(qc))
            if inst.num_edges == 0:
                continue
            for name, algo in all_algos.items():
                try:
                    s = algo(inst)
                    assert s.instance is inst, f"{family.name}/{name}: instance mismatch"
                    edge_set = {e for layer in s.layers for e in layer.edges}
                    assert edge_set == set(
                        range(inst.num_edges)
                    ), f"{family.name}/{name}: missing edges"
                    depth_of = {e: k for k, layer in enumerate(s.layers) for e in layer.edges}
                    for pred, succ in inst.precedence_arcs():
                        assert depth_of[pred] < depth_of[succ], (
                            f"{family.name}/{name}: precedence arc " f"({pred}, {succ}) violated"
                        )
                except Exception as exc:
                    errors.append(f"{family.name}/{name}: {exc}")

        assert not errors, "\n".join(errors)
