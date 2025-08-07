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

"""replace_edges_with_one_edge"""

from typing import TypeVar

from rustworkx.rustworkx import PyDiGraph

from ..aliases import EdgeIndex, NodeIndex

T = TypeVar("T")
S = TypeVar("S")


def replace_edges_with_one_edge(
    graph: PyDiGraph[T, S],
    parent_idx: NodeIndex,
    child_idx: NodeIndex,
    new_edge: S,
) -> EdgeIndex:
    """Replace all the parallel edges between two nodes with a single edge.

    Args:
        graph: The graph to mutate.
        parent_idx: The index of the parent node.
        child_idx: The index of the child node.
        new_edge: The new edge.

    Returns:
        The indices of the new edges.
    """
    for edge in graph.edge_indices_from_endpoints(parent_idx, child_idx):
        graph.remove_edge_from_index(edge)

    return graph.add_edge(parent_idx, child_idx, new_edge)
