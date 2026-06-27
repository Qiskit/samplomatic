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

"""Algorithm E — pattern-bucketed batch scheduling (pattern-first, depth-aware)."""

from collections import defaultdict

from ..instance import StratificationInstance
from ..stratification import Layer, Stratification
from ._common import monochromatic_strong_matching


def pattern_batch_stratify(instance: StratificationInstance) -> Stratification:
    """Stratify ``instance`` using pattern-bucketed batch scheduling (Algorithm E).

    At each scheduling round the algorithm groups all *ready* edges (those whose
    precedence predecessors have already been placed) by label, computes a
    maximum-cardinality strong matching for each label bucket, and emits the
    bucket whose matching is largest.  Ties are broken in favour of the label
    with the greatest number of remaining unplaced edges.  The emitted matching
    becomes a new monochromatic layer.

    Because every emitted layer is monochromatic, the output satisfies
    ``unique_pattern_count ≤ len(instance.alphabet)``.

    **Fallback for unique-label circuits**: when every label group's maximum
    matching has cardinality ≤ 1 (e.g. circuits with randomly varied qubit
    pairings where every gate has a distinct label), strict monochromaticity
    would emit one single-gate layer per gate, producing depth and pattern
    count equal to ``|E|``.  In this degenerate case the algorithm instead
    emits a greedy maximum strong matching over *all* ready edges, grouping
    non-conflicting gates with distinct labels into one multi-label layer.
    This simultaneously reduces depth and pattern count while still
    satisfying ``unique_pattern_count ≤ len(instance.alphabet)``.

    This is a one-step lookahead variant of a pure label-round-robin strategy:
    instead of cycling through labels in a fixed order, it always picks the label
    that can contribute the most gates in the current round.

    Args:
        instance: The stratification problem to solve.

    Returns:
        A valid :class:`.Stratification` with
        ``unique_pattern_count ≤ len(instance.alphabet)``.
    """
    if instance.num_edges == 0:
        return Stratification(instance, [])

    labels = instance.labels

    # Readiness tracking: an edge becomes ready when all its predecessors are placed.
    remaining_preds: dict[int, set[int]] = {
        e: set(instance.immediate_predecessors(e)) for e in range(instance.num_edges)
    }
    ready: set[int] = {e for e in range(instance.num_edges) if not remaining_preds[e]}

    # Remaining-edge count per label for tiebreaking.
    remaining_per_label: dict = defaultdict(int)
    for e in range(instance.num_edges):
        remaining_per_label[labels[e]] += 1

    placed: set[int] = set()
    layers: list[Layer] = []

    while ready:
        # Group ready edges by label.
        by_label: dict = defaultdict(list)
        for e in ready:
            by_label[labels[e]].append(e)

        # Find the label whose ready edges yield the largest strong matching.
        best_label = None
        best_matching: frozenset[int] = frozenset()

        for s, cands in by_label.items():
            m = monochromatic_strong_matching(instance, cands)
            # Prefer larger matching; break ties toward the label with most remaining edges.
            if (
                best_label is None
                or len(m) > len(best_matching)
                or (
                    len(m) == len(best_matching)
                    and remaining_per_label[s] > remaining_per_label[best_label]
                )
            ):
                best_label = s
                best_matching = m

        # If every monochromatic matching is trivial (≤ 1 gate) a greedy non-
        # monochromatic layer will contain at least as many gates in one shot,
        # cutting both depth and pattern count.  Emit it instead.
        if len(best_matching) <= 1:
            fallback = monochromatic_strong_matching(instance, list(ready))
            if len(fallback) > len(best_matching):
                best_matching = fallback

        if not best_matching:
            # No progress is possible; this should not occur for a valid instance.
            break

        # Emit the winning matching as a new layer.
        layers.append(Layer(instance, best_matching))

        # Update state: mark placed edges and unlock successors.
        for e in best_matching:
            placed.add(e)
            ready.discard(e)
            remaining_per_label[labels[e]] -= 1
            for s in instance.immediate_successors(e):
                remaining_preds[s].discard(e)
                if not remaining_preds[s] and s not in placed:
                    ready.add(s)

    return Stratification(instance, layers)
