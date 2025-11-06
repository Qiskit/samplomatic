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

from ..aliases import EdgeIndex, NodeIndex

T = TypeVar("T")
S = TypeVar("S")


def replace_nodes_with_one_node(
    graph: PyDiGraph[T, S], node_idxs: Iterable[NodeIndex], new_node: T
) -> tuple[NodeIndex, list[EdgeIndex], list[EdgeIndex]]:
    """Replace given nodes with a single node, preserving all outward/inward edges.

    In addition to the index of the new node, this function returns a list of successor edge indices
    and a list of predecessor edge indices of the new node. These lists are ordered according to the
    order of  ``node_idxs`` in that if ``node_idx_i`` appears before ``node_idx_j``, then all of the
    new edge indices replacing those from ``node_idx_i`` appear in the list before those from
    ``node_idx_j``.

    Args:
        graph: The graph to mutate.
        node_idxs: The connected nodes to replace.
        new_node: The node to replace them with.

    Returns:
        A tuple containing the new node index, the successor edges indices, and the predecessor
        edges indices.
    """
    new_node_idx = graph.add_node(new_node)

    # remove nodes one at a time, re-adding their edges to the new node
    successor_edge_order = []
    predecessor_edge_order = []
    for node_idx in node_idxs:
        for _, child_node_idx, edge_data in graph.out_edges(node_idx):
            successor_edge_order.append(graph.add_edge(new_node_idx, child_node_idx, edge_data))
        for parent_node_idx, _, edge_data in graph.in_edges(node_idx):
            predecessor_edge_order.append(graph.add_edge(parent_node_idx, new_node_idx, edge_data))
        graph.remove_node(node_idx)

    # the above process will have led to all intra-edges of node_idxs to become self-edges; remove
    for parent_node_idx, child_node_idx, _ in graph.out_edges(new_node_idx):
        if parent_node_idx == child_node_idx:
            graph.remove_edge(parent_node_idx, child_node_idx)

    return new_node_idx, successor_edge_order, predecessor_edge_order
