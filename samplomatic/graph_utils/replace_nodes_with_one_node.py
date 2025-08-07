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

"""replace_nodes_with_one_node"""

from collections.abc import Iterable
from typing import TypeVar

from rustworkx.rustworkx import PyDiGraph

from ..aliases import NodeIndex

T = TypeVar("T")
S = TypeVar("S")


def replace_nodes_with_one_node(
    graph: PyDiGraph[T, S], node_idxs: Iterable[NodeIndex], new_node: T
) -> NodeIndex:
    """Replace given nodes with a single node, preserving all outward/inward edges.

    Args:
        graph: The graph to mutate.
        node_idxs: The connected nodes to replace.
        new_node: The node to replace them with.

    Returns:
        The index of the new node in the graph.
    """
    new_node_idx = graph.add_node(new_node)

    # remove nodes one at a time, re-adding their edges to the new node
    for node_idx in node_idxs:
        for _, child_node_idx, edge_data in graph.out_edges(node_idx):
            graph.add_edge(new_node_idx, child_node_idx, edge_data)
        for parent_node_idx, _, edge_data in graph.in_edges(node_idx):
            graph.add_edge(parent_node_idx, new_node_idx, edge_data)
        graph.remove_node(node_idx)

    # the above process will have led to all intra-edges of node_idxs to become self-edges; remove
    for parent_node_idx, child_node_idx, _ in graph.out_edges(new_node_idx):
        if parent_node_idx == child_node_idx:
            graph.remove_edge(parent_node_idx, child_node_idx)

    return new_node_idx
