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

from samplomatic.graph_utils import replace_nodes_with_one_node


def test_replace_single_node():
    """Test replacing a single node with a new one."""
    graph = PyDiGraph()
    a = graph.add_node("a")
    new_node_idx = replace_nodes_with_one_node(graph, [a], "z")

    assert graph.nodes() == ["z"]
    assert graph.num_edges() == 0
    assert new_node_idx >= 0


def test_replace_two_connected_nodes():
    """Test merging connected nodes removes internal edges."""
    graph = PyDiGraph()
    a = graph.add_node("a")
    b = graph.add_node("b")
    graph.add_edge(a, b, "edge")

    new_node_idx = replace_nodes_with_one_node(graph, [a, b], "z")

    assert graph.nodes() == ["z"]
    assert graph.num_edges() == 0
    assert new_node_idx >= 0


def test_edge_preservation():
    """Test merging disconnected nodes preserves external edges."""
    graph = PyDiGraph()
    a = graph.add_node("a")
    b = graph.add_node("b")
    c = graph.add_node("c")
    d = graph.add_node("d")
    graph.add_edge(a, c, "a->c")
    graph.add_edge(b, c, "b->c")
    graph.add_edge(d, a, "d->a")

    new_node_idx = replace_nodes_with_one_node(graph, [a, b], "z")

    assert graph[new_node_idx] == "z"

    out_edges = graph.out_edges(new_node_idx)
    assert len(out_edges) == 2
    assert {child_node_idx for _, child_node_idx, _ in out_edges} == {c}
    assert {edge_data for _, _, edge_data in out_edges} == {"a->c", "b->c"}

    in_edges = graph.in_edges(new_node_idx)
    assert len(in_edges) == 1
    assert {parent_node_idx for parent_node_idx, _, _ in in_edges} == {d}
    assert {edge_data for _, _, edge_data in in_edges} == {"d->a"}
