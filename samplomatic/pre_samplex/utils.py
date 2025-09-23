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

"""Utils"""

from rustworkx import PyDiGraph

from ..aliases import NodeIndex
from ..exceptions import SamplexConstructionError
from ..partition import QubitIndicesPartition
from .graph_data import PreEdge, PreNode, PrePropagate


def pre_propagate_nodes_are_mergeable(
    graph: PyDiGraph[PreNode, PreEdge], node_a_idx: NodeIndex, node_b_idx: NodeIndex
) -> bool:
    """Compare two nodes to check if they are mergeable pre-propagate nodes.

    Args:
        graph: A graph containing the two nodes being checked.
        node_a_idx: The index of the first node.
        node_b_idx: The index of the second node.

    Returns:
        ``True`` if the two nodes are pre-propagate nodes that can be merged
        (same direction, same operation, disjoint subsystems, and common parents),
        ``False`` otherwise.
    """
    node_a = graph[node_a_idx]
    node_b = graph[node_b_idx]

    are_mergeable = (
        isinstance(node_a, PrePropagate)
        and isinstance(node_b, PrePropagate)
        and node_a.spec.mode is node_b.spec.mode
        and node_a.direction == node_b.direction
        and node_a.operation.name == node_b.operation.name
        and not node_a.subsystems.overlaps_with(node_b.subsystems.all_elements)
        and not set(graph.predecessor_indices(node_a_idx)).isdisjoint(
            graph.predecessor_indices(node_b_idx)
        )
    )

    return are_mergeable


def merge_pre_edges(
    graph: PyDiGraph[PreNode, PreEdge], source_idx: NodeIndex, destination_idx: NodeIndex
) -> PreEdge:
    """Merge all pre-edges from two pre-nodes into one pre-edge.

    Args:
        graph: A graph containing the two nodes whose edges are being merged.
        source_idx: The index of the source node.
        destination_idx: The index of the destination node.

    Returns:
        A pre-edge resulting from the merger.
    """
    edges_indices = graph.edge_indices_from_endpoints(source_idx, destination_idx)
    edges = [graph.get_edge_data_by_index(edge_idx) for edge_idx in edges_indices]

    if not edges:
        raise SamplexConstructionError("No edges to merge.")
    elif len(edges) == 1:
        return edges[0]

    directions = set(edge.direction for edge in edges)
    if len(directions) != 1:
        raise SamplexConstructionError("Cannot merge edges with different directions")

    return PreEdge(
        subsystems=QubitIndicesPartition.union(*(edge.subsystems for edge in edges)),
        direction=next(iter(directions)),
        force_register_copy=any(edge.force_register_copy for edge in edges),
    )
