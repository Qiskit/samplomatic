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

"""Internal helpers shared across stratification scheduling algorithms."""

from collections import defaultdict, deque
from collections.abc import Callable, Iterable, Sequence

import rustworkx as rx

from ..instance import StratificationInstance
from ..stratification import Layer, Stratification


def assignment_to_stratification(
    instance: StratificationInstance,
    depth_of: dict[int, int],
) -> Stratification:
    """Convert an edge-to-layer-index mapping into a :class:`.Stratification`.

    Args:
        instance: The stratification problem instance.
        depth_of: Mapping from edge ID to 0-based layer index.  Every edge in
            ``range(instance.num_edges)`` must appear as a key.

    Returns:
        A :class:`.Stratification` whose layers correspond to the groups defined
        by ``depth_of``.
    """
    if not depth_of:
        return Stratification(instance, [])

    layers_dict: dict[int, list[int]] = {}
    for edge, k in depth_of.items():
        layers_dict.setdefault(k, []).append(edge)

    num_layers = max(layers_dict) + 1
    layer_objects = [Layer(instance, layers_dict[k]) for k in range(num_layers) if k in layers_dict]
    return Stratification(instance, layer_objects)


def min_layer_for(
    instance: StratificationInstance,
    e: int,
    depth_of: dict[int, int],
) -> int:
    """Return the earliest layer index at which edge *e* may be placed.

    The result is ``1 + max(depth_of[p] for p in immediate_predecessors(e))``
    when at least one predecessor has already been assigned, otherwise ``0``.

    Args:
        instance: The stratification problem instance.
        e: Edge ID to query.
        depth_of: Partial assignment of edge IDs to layer indices.

    Returns:
        Minimum feasible layer index for *e*.
    """
    preds = instance.immediate_predecessors(e)
    assigned = [depth_of[p] for p in preds if p in depth_of]
    return max(assigned) + 1 if assigned else 0


def slack_window(
    instance: StratificationInstance,
    depth_of: dict[int, int],
) -> dict[int, tuple[int, int]]:
    """Compute the [d_min, d_max] slack window for every edge given a complete assignment.

    ``d_min`` is the earliest layer allowed by precedence constraints;
    ``d_max`` is the latest layer that does not delay any successor beyond its
    current position.

    Args:
        instance: The stratification problem instance.
        depth_of: Complete mapping of every edge ID to its current layer index.

    Returns:
        Dictionary mapping each edge ID to a ``(d_min, d_max)`` pair.
    """
    if not depth_of:
        return {}

    global_max = max(depth_of.values())
    windows: dict[int, tuple[int, int]] = {}

    for e in range(instance.num_edges):
        preds = instance.immediate_predecessors(e)
        pred_depths = [depth_of[p] for p in preds if p in depth_of]
        d_min = max(pred_depths) + 1 if pred_depths else 0

        succs = instance.immediate_successors(e)
        succ_depths = [depth_of[s] for s in succs if s in depth_of]
        d_max = min(succ_depths) - 1 if succ_depths else global_max

        windows[e] = (d_min, d_max)

    return windows


def pack_into_layers(
    instance: StratificationInstance,
    ordering: Sequence[int],
    *,
    layer_choice: Callable[[int, list[set[int]], list[set], int], int] | None = None,
) -> dict[int, int]:
    """Classical list scheduler: assign each edge to the earliest conflict-free layer.

    Walks *ordering* and for each edge finds the smallest layer index ``k >=
    d_min`` such that ``k``'s occupied vertices do not overlap the edge's
    vertices.  A custom *layer_choice* callable can override this selection.

    Args:
        instance: The stratification problem instance.
        ordering: Sequence of edge IDs in the order they should be scheduled.
            Must be a linear extension of the precedence partial order.
        layer_choice: Optional callable ``(e, layers_vertices, layers_patterns, d_min)
            -> k`` that chooses the target layer index.  Receives the mutable
            layer-vertex and layer-pattern lists; may append new entries by
            returning an index equal to ``len(layers_vertices)``.

    Returns:
        Dictionary mapping every edge ID in *ordering* to its assigned layer index.
    """
    depth_of: dict[int, int] = {}
    layers_vertices: list[set[int]] = []
    layers_patterns: list[set] = []
    hg_edges = instance.hypergraph.edges
    labels = instance.labels

    for e in ordering:
        e_verts = hg_edges[e]
        d_min = min_layer_for(instance, e, depth_of)

        if layer_choice is not None:
            k = layer_choice(e, layers_vertices, layers_patterns, d_min)
        else:
            k = d_min
            while k < len(layers_vertices) and (layers_vertices[k] & e_verts):
                k += 1

        # Extend lists to accommodate index k.
        while len(layers_vertices) <= k:
            layers_vertices.append(set())
            layers_patterns.append(set())

        layers_vertices[k].update(e_verts)
        layers_patterns[k].add(labels[e])
        depth_of[e] = k

    return depth_of


def monochromatic_strong_matching(
    instance: StratificationInstance,
    candidates: Iterable[int],
) -> frozenset[int]:
    """Return a maximum-cardinality strong matching from *candidates*.

    A *strong matching* is a subset of edges that are pairwise vertex-disjoint
    (no two edges share a vertex).  For hypergraphs whose candidate edges all
    have arity ≤ 2, an exact maximum-cardinality matching is found via
    :func:`rustworkx.max_weight_matching`.  For higher-arity candidates a
    greedy approach is used.

    Args:
        instance: The stratification problem instance.
        candidates: Iterable of edge IDs from which to build the matching.

    Returns:
        A :class:`frozenset` of edge IDs forming a strong matching.
    """
    hg_edges = instance.hypergraph.edges
    cands = list(candidates)

    if not cands:
        return frozenset()

    max_arity = max(len(hg_edges[e]) for e in cands)

    if max_arity <= 2:
        size1 = [e for e in cands if len(hg_edges[e]) == 1]
        size2 = [e for e in cands if len(hg_edges[e]) == 2]

        result: set[int] = set()
        used: set[int] = set()

        if size2:
            g: rx.PyGraph = rx.PyGraph()
            qubit_node: dict[int, int] = {}
            # Maps frozenset({u_node, v_node}) -> deque of edge IDs sharing that node pair.
            node_pair_edges: dict[frozenset, deque] = defaultdict(deque)

            for e in size2:
                u, v = sorted(hg_edges[e])
                for q in (u, v):
                    if q not in qubit_node:
                        qubit_node[q] = g.add_node(q)
                un, vn = qubit_node[u], qubit_node[v]
                g.add_edge(un, vn, e)
                node_pair_edges[frozenset({un, vn})].append(e)

            matched_pairs = rx.max_weight_matching(g, max_cardinality=True)
            for un, vn in matched_pairs:
                key = frozenset({un, vn})
                if node_pair_edges[key]:
                    e = node_pair_edges[key].popleft()
                    result.add(e)
                    used.update(hg_edges[e])

        for e in size1:
            q = next(iter(hg_edges[e]))
            if q not in used:
                result.add(e)
                used.add(q)

        return frozenset(result)

    # Greedy maximal matching for higher-arity edges.
    result_set: set[int] = set()
    occupied: set[int] = set()
    for e in sorted(cands, key=lambda x: (-len(hg_edges[x]), x)):
        if not (hg_edges[e] & occupied):
            result_set.add(e)
            occupied.update(hg_edges[e])
    return frozenset(result_set)
