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

"""Local-search post-pass for stratification refinement."""

from collections.abc import Hashable
from typing import Literal

from ..stratification import Stratification
from ._common import assignment_to_stratification, slack_window


def _compute_key(
    depth_of: dict[int, int],
    labels: tuple[Hashable, ...],
    key: Literal["depth", "pattern"],
) -> tuple[int, int]:
    """Compute the lex comparison key directly from a ``depth_of`` mapping.

    Avoids constructing :class:`.Layer` and :class:`.Stratification` objects.

    Args:
        depth_of: Complete edge-to-layer-index mapping.
        labels: Label tuple for the instance (parallel to edge indices).
        key: Which lex key to return.

    Returns:
        ``(depth, unique_pattern_count)`` when ``key="depth"``, or
        ``(unique_pattern_count, depth)`` when ``key="pattern"``.
    """
    if not depth_of:
        return (0, 0)

    d = max(depth_of.values()) + 1

    # Build one frozenset of labels per layer, then count distinct frozensets.
    layer_label_sets: list[set[Hashable]] = [set() for _ in range(d)]
    for e, k in depth_of.items():
        layer_label_sets[k].add(labels[e])

    upc = len({frozenset(s) for s in layer_label_sets if s})

    return (d, upc) if key == "depth" else (upc, d)


def refine_stratification(
    stratification: Stratification,
    *,
    key: Literal["depth", "pattern"] = "depth",
    max_passes: int = 100,
) -> Stratification:
    """Post-process ``stratification`` with local-search moves to improve the objective.

    Three move types are attempted:

    - **Relocate**: move a single edge ``e`` from its current layer to any other layer
      within its slack window ``[d_min, d_max]`` that is still a valid strong matching.
    - **Swap**: exchange edges ``e ∈ L_k`` and ``f ∈ L_{k'}`` if both layers remain
      valid strong matchings after the swap and both edges stay within their slack windows.
    - **Merge**: collapse two adjacent layers ``L_k, L_{k+1}`` into one, if their union
      is a valid layer (antichain and strong matching).

    A move is accepted only if it strictly improves the lex key:
    ``(depth, unique_pattern_count)`` for ``key="depth"`` or
    ``(unique_pattern_count, depth)`` for ``key="pattern"``.

    The search loops until no improving move is found (steepest descent) or ``max_passes``
    is reached.  **The input stratification is never modified**; a new one is returned.

    Args:
        stratification: The starting stratification to improve.
        key: The comparison key governing acceptance.
        max_passes: Maximum number of steepest-descent passes.

    Returns:
        A new :class:`.Stratification` that is at least as good as the input under ``key``.
    """
    instance = stratification.instance
    if instance.num_edges == 0:
        return stratification

    hg_edges = instance.hypergraph.edges
    labels = instance.labels

    # Mutable working copy of the assignment.
    depth_of: dict[int, int] = {
        e: k for k, layer in enumerate(stratification.layers) for e in layer.edges
    }

    # Per-layer vertex occupancy and label-count bookkeeping for O(1) conflict checks.
    num_layers = stratification.depth
    layer_verts: list[set[int]] = [set() for _ in range(num_layers)]
    layer_label_counts: list[dict[Hashable, int]] = [{} for _ in range(num_layers)]

    for e, k in depth_of.items():
        layer_verts[k].update(hg_edges[e])
        lbl = labels[e]
        layer_label_counts[k][lbl] = layer_label_counts[k].get(lbl, 0) + 1

    def _get_key() -> tuple[int, int]:
        """Compute the current lex key from live mutable state."""
        if not depth_of:
            return (0, 0)
        d = max(depth_of.values()) + 1
        patterns: set[frozenset[Hashable]] = set()
        for lc in layer_label_counts[:d]:
            if lc:
                patterns.add(frozenset(lc.keys()))
        upc = len(patterns)
        return (d, upc) if key == "depth" else (upc, d)

    def _relocate_edge(e: int, old_k: int, new_k: int) -> None:
        """Move edge *e* from layer *old_k* to layer *new_k* in-place."""
        lbl = labels[e]
        e_verts = hg_edges[e]
        # Remove from old layer.
        layer_verts[old_k].difference_update(e_verts)
        layer_label_counts[old_k][lbl] -= 1
        if layer_label_counts[old_k][lbl] == 0:
            del layer_label_counts[old_k][lbl]
        # Add to new layer.
        layer_verts[new_k].update(e_verts)
        layer_label_counts[new_k][lbl] = layer_label_counts[new_k].get(lbl, 0) + 1
        depth_of[e] = new_k

    def _apply_swap(e: int, ke: int, f: int, kf: int) -> None:
        """Atomically swap *e* and *f* between layers *ke* and *kf*.

        Removes both edges first, then re-inserts them into their new layers.
        This avoids transient states where two overlapping edges share a layer,
        which would corrupt the ``layer_verts`` bookkeeping.
        """
        e_verts = hg_edges[e]
        f_verts = hg_edges[f]
        se = labels[e]
        sf = labels[f]
        # Remove both edges from their current layers.
        layer_verts[ke].difference_update(e_verts)
        layer_label_counts[ke][se] -= 1
        if layer_label_counts[ke][se] == 0:
            del layer_label_counts[ke][se]
        layer_verts[kf].difference_update(f_verts)
        layer_label_counts[kf][sf] -= 1
        if layer_label_counts[kf][sf] == 0:
            del layer_label_counts[kf][sf]
        # Re-insert into swapped positions.
        layer_verts[kf].update(e_verts)
        layer_label_counts[kf][se] = layer_label_counts[kf].get(se, 0) + 1
        layer_verts[ke].update(f_verts)
        layer_label_counts[ke][sf] = layer_label_counts[ke].get(sf, 0) + 1
        depth_of[e] = kf
        depth_of[f] = ke

    current = _get_key()

    for _ in range(max_passes):
        # Resync bookkeeping from depth_of at the start of each pass.  This is O(|E|)
        # per pass and guards against any accumulated bookkeeping drift.
        for lv in layer_verts:
            lv.clear()
        for lc in layer_label_counts:
            lc.clear()
        for e, k in depth_of.items():
            layer_verts[k].update(hg_edges[e])
            lc = layer_label_counts[k]
            lc[labels[e]] = lc.get(labels[e], 0) + 1

        improved = False
        windows = slack_window(instance, depth_of)

        # ----------------------------------------------------------------
        # Relocate moves: shift one edge to another feasible layer.
        # ----------------------------------------------------------------
        for e in range(instance.num_edges):
            d_min, d_max = windows[e]
            old_k = depth_of[e]
            e_verts = hg_edges[e]

            for new_k in range(d_min, d_max + 1):
                if new_k == old_k:
                    continue
                # Vertex-conflict check against the target layer (e is not in it yet).
                if layer_verts[new_k] & e_verts:
                    continue

                _relocate_edge(e, old_k, new_k)
                new_key = _get_key()
                if new_key < current:
                    current = new_key
                    improved = True
                    break
                else:
                    _relocate_edge(e, new_k, old_k)

            if improved:
                break

        if improved:
            continue

        # ----------------------------------------------------------------
        # Swap moves: exchange two edges in different layers.
        # ----------------------------------------------------------------
        edge_list = list(range(instance.num_edges))
        for i, e in enumerate(edge_list):
            for f in edge_list[i + 1 :]:
                ke = depth_of[e]
                kf = depth_of[f]
                if ke == kf:
                    continue

                d_min_e, d_max_e = windows[e]
                d_min_f, d_max_f = windows[f]
                # Both edges must lie within their slack windows after the swap.
                if not (d_min_e <= kf <= d_max_e and d_min_f <= ke <= d_max_f):
                    continue

                e_verts = hg_edges[e]
                f_verts = hg_edges[f]

                # Check that f does not conflict with the remaining edges at ke.
                if (layer_verts[ke] - e_verts) & f_verts:
                    continue
                # Check that e does not conflict with the remaining edges at kf.
                if (layer_verts[kf] - f_verts) & e_verts:
                    continue

                # Atomically swap the two edges (remove both first, then re-insert).
                _apply_swap(e, ke, f, kf)
                new_key = _get_key()
                if new_key < current:
                    current = new_key
                    improved = True
                    break
                else:
                    # Undo via the same atomic helper.
                    _apply_swap(e, kf, f, ke)

            if improved:
                break

        if improved:
            continue

        # ----------------------------------------------------------------
        # Merge moves: collapse two adjacent layers into one.
        # ----------------------------------------------------------------
        cur_num_layers = max(depth_of.values()) + 1 if depth_of else 0

        for k in range(cur_num_layers - 1):
            edges_k = [e for e, ek in depth_of.items() if ek == k]
            edges_k1 = [e for e, ek in depth_of.items() if ek == k + 1]
            combined = edges_k + edges_k1

            # is_layer checks both antichain (no e≺f pairs) and strong matching.
            if not instance.is_layer(combined):
                continue

            # Build the candidate assignment: merge k+1 into k, shift higher layers down.
            new_depth: dict[int, int] = {}
            for e, ek in depth_of.items():
                if ek == k + 1:
                    new_depth[e] = k
                elif ek > k + 1:
                    new_depth[e] = ek - 1
                else:
                    new_depth[e] = ek

            candidate_key = _compute_key(new_depth, labels, key)
            if candidate_key < current:
                # Commit: update depth_of in-place and rebuild layer structures.
                depth_of.clear()
                depth_of.update(new_depth)
                new_num = max(depth_of.values()) + 1 if depth_of else 0
                layer_verts.clear()
                layer_label_counts.clear()
                for _ in range(new_num):
                    layer_verts.append(set())
                    layer_label_counts.append({})
                for e, ek in depth_of.items():
                    layer_verts[ek].update(hg_edges[e])
                    lbl = labels[e]
                    layer_label_counts[ek][lbl] = layer_label_counts[ek].get(lbl, 0) + 1
                current = candidate_key
                improved = True
                break

        if not improved:
            break  # Local optimum reached — no move improved the objective.

    return assignment_to_stratification(instance, depth_of)
