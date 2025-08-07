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

"""cluster_compatible_nodes"""

from collections.abc import Callable, Iterator
from typing import TypeVar

from rustworkx.rustworkx import PyDiGraph, topological_generations

from ..aliases import NodeIndex

T = TypeVar("T")
S = TypeVar("S")


def cluster_compatible_nodes(
    graph: PyDiGraph[T, S],
    compare_fn: Callable[[PyDiGraph[T, S], NodeIndex, NodeIndex], bool],
) -> Iterator[list[NodeIndex]]:
    """Yield clusters of nodes that are all pairwise compatible according to ``compare_fn``.

    This function partitions the graph into topological generations, then yields clusters of
    equivalent nodes that belong to the same generation.

    Args:
        graph: The graph to yield topological generations for.
        compare_fn: An equivalence function between pairs of nodes that returns booleans.

    Yields:
        Lists of nodes, where each list is a maximal weakly connected set of nodes that
        are all pairwise compatible according to ``compare_fn``.
    """
    for generation in topological_generations(graph):
        clusters = []

        for node_idx in generation:
            for cluster in clusters:
                if all(
                    compare_fn(graph, node_idx, clustered_node_idx)
                    for clustered_node_idx in cluster
                ):
                    cluster.append(node_idx)
                    break
            else:
                clusters.append([node_idx])
        yield from clusters
