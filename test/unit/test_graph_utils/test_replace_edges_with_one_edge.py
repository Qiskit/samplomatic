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

from rustworkx.rustworkx import PyDiGraph

from samplomatic.graph_utils import replace_edges_with_one_edge


def test_replace_when_no_edges_present():
    """Test `replace_edges` when parent and child are not connected."""
    graph = PyDiGraph()
    a = graph.add_node("a")
    b = graph.add_node("b")
    assert not graph.edge_indices_from_endpoints(a, b)

    new_edge_idx = replace_edges_with_one_edge(graph, a, b, "ab")
    assert graph.edge_indices_from_endpoints(a, b) == [new_edge_idx]
    assert graph.edges() == ["ab"]


def test_replace_when_multiple_edges_present():
    """Test `replace_edges` when parent and child are connected by multiple edges."""
    graph = PyDiGraph()
    a = graph.add_node("a")
    b = graph.add_node("b")
    graph.add_edge(a, b, "ab0")
    graph.add_edge(a, b, "ab1")
    graph.add_edge(b, a, "ba0")
    graph.add_edge(a, b, "ab2")
    graph.add_edge(a, b, "ab3")
    graph.add_edge(b, a, "ba1")
    assert len(graph.edges()) == 6

    ab_edge_idxs = replace_edges_with_one_edge(graph, a, b, "ab")
    assert len(graph.edges()) == 3

    ba_edge_idxs = replace_edges_with_one_edge(graph, b, a, "ba")
    assert len(graph.edges()) == 2

    assert set(graph.edge_indices()) == {ab_edge_idxs, ba_edge_idxs}
    assert set(graph.edges()) == {"ab", "ba"}
