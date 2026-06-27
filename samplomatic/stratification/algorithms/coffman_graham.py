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

"""Algorithm B — Coffman–Graham list scheduling with pattern tiebreaker."""

from ..instance import StratificationInstance
from ..stratification import Stratification
from ._common import assignment_to_stratification, min_layer_for


def coffman_graham_stratify(instance: StratificationInstance) -> Stratification:
    """Stratify ``instance`` using Coffman–Graham scheduling with a pattern-reuse tiebreaker.

    Orders edges by longest chain first (``chain_height`` descending, then edge arity
    descending, then edge ID ascending) and maintains a *ready* set of edges whose
    predecessors have all been placed.  For each round the highest-priority ready edge is
    selected.  Among feasible layer indices for that edge, the algorithm prefers a layer
    whose current label set already contains the edge's label (*reuse*), falling back to
    the smallest feasible layer (*grow*).

    This keeps depth close to the Coffman–Graham bound while opportunistically reducing
    the unique-pattern count without backtracking.

    Time complexity: ``O(|E| · (m + log |E|))`` where ``m`` is the output depth.

    Args:
        instance: The stratification problem to solve.

    Returns:
        A valid :class:`.Stratification`.
    """
    if instance.num_edges == 0:
        return Stratification(instance, [])

    hg_edges = instance.hypergraph.edges
    labels = instance.labels

    # Build predecessor/successor adjacency for readiness tracking.
    remaining_preds: dict[int, set[int]] = {
        e: set(instance.immediate_predecessors(e)) for e in range(instance.num_edges)
    }
    immediate_succs: dict[int, frozenset[int]] = {
        e: instance.immediate_successors(e) for e in range(instance.num_edges)
    }

    # Initialise ready set: edges with no predecessors.
    ready: set[int] = {e for e in range(instance.num_edges) if not remaining_preds[e]}

    depth_of: dict[int, int] = {}
    layers_vertices: list[set[int]] = []
    layers_patterns: list[set] = []

    def _priority(e: int) -> tuple:
        """Lower value = higher priority (for use with ``min``)."""
        return (-instance.chain_height(e), -len(hg_edges[e]), e)

    while ready:
        # Pick the highest-priority ready edge.
        e = min(ready, key=_priority)
        ready.discard(e)

        e_verts = hg_edges[e]
        label = labels[e]
        d_min = min_layer_for(instance, e, depth_of)

        # Partition feasible layer indices into reuse (label already present) and grow.
        reuse_ks: list[int] = []
        grow_ks: list[int] = []
        for k in range(d_min, len(layers_vertices) + 1):
            # k == len(layers_vertices) means opening a brand-new layer.
            if k == len(layers_vertices) or not (layers_vertices[k] & e_verts):
                if k < len(layers_vertices) and label in layers_patterns[k]:
                    reuse_ks.append(k)
                else:
                    grow_ks.append(k)

        k = min(reuse_ks) if reuse_ks else min(grow_ks)

        # Extend layer lists to accommodate index k.
        while len(layers_vertices) <= k:
            layers_vertices.append(set())
            layers_patterns.append(set())

        layers_vertices[k].update(e_verts)
        layers_patterns[k].add(label)
        depth_of[e] = k

        # Unlock successors whose last predecessor was just placed.
        for s in immediate_succs[e]:
            remaining_preds[s].discard(e)
            if not remaining_preds[s]:
                ready.add(s)

    return assignment_to_stratification(instance, depth_of)
