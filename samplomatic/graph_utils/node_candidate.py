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

"""NodeCandidate"""

from typing import Generic, TypeVar

from rustworkx.rustworkx import PyDiGraph

from ..aliases import NodeIndex

T = TypeVar("T")
S = TypeVar("S")


class NodeCandidate(Generic[T, S]):
    """A node that we want to add to the graph, but not yet.

    The node is only added when we ask for its :attr:`node_idx` in the graph.

    Args:
        graph: The graph to add the node to.
        node: The node data for the node to add.
    """

    def __init__(self, graph: PyDiGraph[T, S], node: T):
        self.graph = graph
        self.node = node
        self._node_idx = None

    @property
    def node_idx(self) -> NodeIndex:
        """The node index in the graph."""
        if (node_idx := self._node_idx) is None:
            self._node_idx = node_idx = self.graph.add_node(self.node)
        return node_idx

    @property
    def is_added(self) -> bool:
        """Whether the node has yet been added to the graph."""
        return self._node_idx is not None
