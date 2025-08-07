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

"""prune_unreachable_nodes"""

from collections.abc import Sequence

from rustworkx.rustworkx import PyDiGraph, digraph_dfs_edges

from ..aliases import NodeIndex


def find_unreachable_nodes(graph: PyDiGraph, start_idxs: Sequence[NodeIndex]) -> set[NodeIndex]:
    """Find all nodes from the graph that are not reachable from the start nodes.

    Args:
        graph: The graph to search.
        start_idxs: The node indices to start from.

    Returns:
        A set of the unreachable node indices.
    """
    # find all reachable nodes
    reachable = set()
    for start in start_idxs:
        for _, node_idx in digraph_dfs_edges(graph, start):
            reachable.add(node_idx)
        reachable.add(start)

    return set(graph.node_indices()) - reachable
