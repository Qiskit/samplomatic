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

"""Algorithm G — GRASP randomized multi-start."""

import bisect
from typing import Literal

import numpy as np

from ..instance import StratificationInstance
from ..stratification import Stratification
from ._common import assignment_to_stratification, min_layer_for


def _grasp_greedy(
    instance: StratificationInstance,
    alpha: float,
    rng: np.random.Generator,
) -> dict[int, int]:
    """Randomized version of Algorithm A (greedy list scheduling).

    At each step a restricted candidate list (RCL) is built from all ready edges whose
    ``chain_height`` score lies within ``alpha`` of the maximum.  One candidate is chosen
    uniformly at random from the RCL.
    """
    if instance.num_edges == 0:
        return {}

    hg_edges = instance.hypergraph.edges
    remaining_preds: dict[int, set[int]] = {
        e: set(instance.immediate_predecessors(e)) for e in range(instance.num_edges)
    }
    immediate_succs: dict[int, frozenset[int]] = {
        e: instance.immediate_successors(e) for e in range(instance.num_edges)
    }

    # Keep ready list sorted (ascending) for deterministic RCL construction order.
    ready: list[int] = sorted(e for e in range(instance.num_edges) if not remaining_preds[e])

    height: list[int] = [instance.chain_height(e) for e in range(instance.num_edges)]

    depth_of: dict[int, int] = {}
    layers_vertices: list[set[int]] = []
    layers_patterns: list[set] = []

    while ready:
        scores = [height[e] for e in ready]
        s_max = max(scores)
        s_min = min(scores)
        threshold = s_max - alpha * (s_max - s_min)
        rcl = [e for e, s in zip(ready, scores) if s >= threshold]

        e = rcl[int(rng.integers(len(rcl)))]
        ready.remove(e)

        e_verts = hg_edges[e]
        d_min = min_layer_for(instance, e, depth_of)
        k = d_min
        while k < len(layers_vertices) and layers_vertices[k] & e_verts:
            k += 1

        while len(layers_vertices) <= k:
            layers_vertices.append(set())
            layers_patterns.append(set())

        layers_vertices[k].update(e_verts)
        layers_patterns[k].add(instance.labels[e])
        depth_of[e] = k

        for s in immediate_succs[e]:
            remaining_preds[s].discard(e)
            if not remaining_preds[s]:
                bisect.insort(ready, s)

    return depth_of


def _grasp_coffman_graham(
    instance: StratificationInstance,
    alpha: float,
    rng: np.random.Generator,
) -> dict[int, int]:
    """Randomized version of Algorithm B (Coffman–Graham with pattern-reuse tiebreaker).

    The randomization is applied to *edge selection*: at each step a restricted candidate
    list (RCL) is built from all ready edges whose ``chain_height`` score lies within
    ``alpha`` of the maximum (identical to how :func:`_grasp_greedy` works).  One edge is
    chosen uniformly at random from the RCL.

    Once an edge is chosen, Algorithm B's *deterministic* layer-selection policy is applied
    unchanged: among feasible layer indices, prefer the earliest layer that already contains
    the edge's label (*reuse*), falling back to the earliest layer that does not (*grow*).
    This preserves the pattern-reuse benefit of Algorithm B while exploring a diverse set
    of edge-ordering trajectories across GRASP restarts.
    """
    if instance.num_edges == 0:
        return {}

    hg_edges = instance.hypergraph.edges
    labels = instance.labels

    remaining_preds: dict[int, set[int]] = {
        e: set(instance.immediate_predecessors(e)) for e in range(instance.num_edges)
    }
    immediate_succs: dict[int, frozenset[int]] = {
        e: instance.immediate_successors(e) for e in range(instance.num_edges)
    }

    # Sorted list for deterministic RCL construction order within the same score tier.
    ready: list[int] = sorted(e for e in range(instance.num_edges) if not remaining_preds[e])

    height: list[int] = [instance.chain_height(e) for e in range(instance.num_edges)]

    depth_of: dict[int, int] = {}
    layers_vertices: list[set[int]] = []
    layers_patterns: list[set] = []

    while ready:
        # Build RCL over ready edges by chain_height score (same as _grasp_greedy).
        scores = [height[e] for e in ready]
        s_max = max(scores)
        s_min = min(scores)
        threshold = s_max - alpha * (s_max - s_min)
        rcl = [e for e, s in zip(ready, scores) if s >= threshold]

        e = rcl[int(rng.integers(len(rcl)))]
        ready.remove(e)

        e_verts = hg_edges[e]
        label = labels[e]
        d_min = min_layer_for(instance, e, depth_of)

        # Algorithm B's deterministic layer-selection: reuse preferred, else earliest grow.
        reuse_ks: list[int] = []
        grow_ks: list[int] = []
        for k in range(d_min, len(layers_vertices) + 1):
            if k == len(layers_vertices) or not (layers_vertices[k] & e_verts):
                if k < len(layers_vertices) and label in layers_patterns[k]:
                    reuse_ks.append(k)
                else:
                    grow_ks.append(k)

        chosen_k = min(reuse_ks) if reuse_ks else min(grow_ks)

        while len(layers_vertices) <= chosen_k:
            layers_vertices.append(set())
            layers_patterns.append(set())

        layers_vertices[chosen_k].update(e_verts)
        layers_patterns[chosen_k].add(label)
        depth_of[e] = chosen_k

        for s in immediate_succs[e]:
            remaining_preds[s].discard(e)
            if not remaining_preds[s]:
                bisect.insort(ready, s)

    return depth_of


def grasp_stratify(
    instance: StratificationInstance,
    *,
    base: Literal["greedy", "coffman_graham"] = "coffman_graham",
    restarts: int = 20,
    alpha: float = 0.2,
    key: Literal["depth", "pattern"] = "depth",
    seed: int | None = None,
) -> Stratification:
    """Stratify ``instance`` using GRASP randomized multi-start (Algorithm G).

    Runs ``restarts`` independent randomized trials of the underlying heuristic, each
    seeded differently.  In every trial, at each scheduling step a *restricted candidate
    list* (RCL) is built from all ready edges whose ``chain_height`` score lies within
    ``α`` of the maximum:

    .. code-block:: text

        RCL = {e : chain_height(e) ≥ s_max − α · (s_max − s_min)}

    One edge is chosen uniformly at random from the RCL.  Once chosen, the base
    algorithm's layer-selection policy is applied *deterministically* — so for
    ``"coffman_graham"`` the pattern-reuse tiebreaker is always honoured.

    Setting ``α = 0`` makes the RCL a singleton (best score only); when there are no
    ties in ``chain_height`` this recovers the deterministic base exactly.

    The best stratification across all trials (under ``key``) is returned.

    Args:
        instance: The stratification problem to solve.
        base: The underlying heuristic to randomize.  ``"greedy"`` or
            ``"coffman_graham"`` (default).
        restarts: Number of independent randomized trials.
        alpha: RCL parameter ``α ∈ [0, 1]``.  ``0`` = fully greedy (deterministic),
            ``1`` = fully random.
        key: Comparison key for selecting the best result.  ``"depth"`` uses
            ``(depth, unique_pattern_count)``; ``"pattern"`` uses
            ``(unique_pattern_count, depth)``.
        seed: Optional seed for :class:`numpy.random.Generator`.  Pass an integer
            for reproducible results across multiple calls.

    Returns:
        The best :class:`.Stratification` found across all trials.
    """
    if instance.num_edges == 0:
        return Stratification(instance, [])

    rng = np.random.default_rng(seed)
    key_fn = (lambda s: s.key_depth_first) if key == "depth" else (lambda s: s.key_pattern_first)

    best: Stratification | None = None

    for _ in range(restarts):
        trial_rng = np.random.default_rng(int(rng.integers(2**31)))

        if base == "greedy":
            depth_of = _grasp_greedy(instance, alpha, trial_rng)
        elif base == "coffman_graham":
            depth_of = _grasp_coffman_graham(instance, alpha, trial_rng)
        else:
            raise ValueError(
                f"Unknown base algorithm: {base!r}.  Expected one of 'greedy', 'coffman_graham'."
            )

        strat = assignment_to_stratification(instance, depth_of)
        if best is None or key_fn(strat) < key_fn(best):
            best = strat

    # best is not None because restarts >= 1 and num_edges > 0.
    assert best is not None
    return best
