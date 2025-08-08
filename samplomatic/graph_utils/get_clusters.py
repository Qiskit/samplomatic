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

"""get_clusters"""

from collections.abc import Callable, Iterator
from typing import TypeVar

from rustworkx.rustworkx import PyDiGraph, weakly_connected_components

from ..aliases import NodeIndex

T = TypeVar("T")
S = TypeVar("S")


def get_clusters(
    graph: PyDiGraph[T, S], filter_fn: Callable[[T], bool]
) -> Iterator[list[NodeIndex]]:
    """Yield lists of nodes that all pass the filter and are connected in the graph.

    Args:
        graph: The graph to search.
        filter_fn: A filter function acting on node data that returns booleans.

    Yields:
        Lists of nodes, where each list is a maximal weakly connected set of nodes that
        all pass the filter.
    """
    filtered_nodes = graph.filter_nodes(filter_fn)
    filtered_graph = graph.subgraph(filtered_nodes)
    for component in weakly_connected_components(filtered_graph):
        yield [filtered_nodes[subgraph_node_idx] for subgraph_node_idx in component]
