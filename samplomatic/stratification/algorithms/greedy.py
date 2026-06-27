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

"""Algorithm A — greedy list scheduling (depth-first)."""

from ..instance import StratificationInstance
from ..stratification import Stratification
from ._common import assignment_to_stratification, pack_into_layers


def greedy_stratify(instance: StratificationInstance) -> Stratification:
    """Stratify ``instance`` using greedy list scheduling (Algorithm A).

    Processes edges in a linear extension of the precedence partial order ``≺``
    and packs each edge into the earliest layer where it does not conflict with
    already-placed edges.  Gate labels (patterns) are ignored entirely; this is
    the classical layered scheduler that minimises circuit depth.

    The resulting depth equals the length of the longest antichain-free chain in
    ``instance``, which is optimal.

    Time complexity: ``O(|E| · m · max_e |e|)`` where ``m`` is the output depth
    and ``|e|`` is the arity of edge ``e``.

    Args:
        instance: The stratification problem to solve.

    Returns:
        A valid :class:`.Stratification` whose depth is optimal.
    """
    if instance.num_edges == 0:
        return Stratification(instance, [])

    ordering = instance.linear_extension()
    depth_of = pack_into_layers(instance, ordering)
    return assignment_to_stratification(instance, depth_of)
