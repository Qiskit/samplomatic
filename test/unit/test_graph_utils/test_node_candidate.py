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

"""Test NodeCandidate"""

from rustworkx.rustworkx import PyDiGraph

from samplomatic.graph_utils import NodeCandidate


def test_construct():
    """Test constructing the candidate."""
    graph = PyDiGraph()
    candidate = NodeCandidate(graph, object())

    assert not candidate.is_added
    assert not any(graph.nodes())


def test_node_idx():
    """Test getting the node index makes a node."""
    graph = PyDiGraph()
    candidate = NodeCandidate(graph, val := object())

    assert not candidate.is_added
    node_idx = candidate.node_idx
    assert candidate.is_added
    assert graph.node_indices() == [node_idx]
    assert graph[node_idx] is val
