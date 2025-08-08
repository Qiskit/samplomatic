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

from samplomatic.graph_utils import cluster_compatible_nodes


def test_empty_graph():
    """Test edge case of an empty graph."""
    graph = PyDiGraph()
    assert not list(cluster_compatible_nodes(graph, lambda graph, y, z: False))
    assert not list(cluster_compatible_nodes(graph, lambda graph, y, z: True))


def test_compare_is_always_false():
    """Test that there are no clusters when the filter is always False."""
    graph = PyDiGraph()
    a = graph.add_node("a")
    b = graph.add_node("b")
    c = graph.add_node("c")
    d = graph.add_node("d")
    e = graph.add_node("e")
    graph.add_edge(a, b, None)
    graph.add_edge(a, c, None)
    graph.add_edge(b, d, None)
    graph.add_edge(c, e, None)

    expected = [[0], [2], [1], [4], [3]]
    assert list(cluster_compatible_nodes(graph, lambda graph, y, z: False)) == expected


def test_compare_is_always_true():
    """Test that the right clusters are formed when the filter is always True."""
    graph = PyDiGraph()
    a = graph.add_node("a")
    b = graph.add_node("b")
    c = graph.add_node("c")
    d = graph.add_node("d")
    e = graph.add_node("e")
    graph.add_edge(a, b, None)
    graph.add_edge(a, c, None)
    graph.add_edge(b, d, None)
    graph.add_edge(c, e, None)

    expected = [[0], [2, 1], [4, 3]]
    assert list(cluster_compatible_nodes(graph, lambda graph, y, z: True)) == expected


def test_non_trivial_compare_fn():
    """Test with a non-trivial ``compare_fn``."""

    def compare_fn(graph, node_a_idx, node_b_idx):
        """True if the two nodes are both capitalized or not, False otherwise."""
        return graph[node_a_idx].isupper() == graph[node_b_idx].isupper()

    graph = PyDiGraph()
    a = graph.add_node("a")
    b = graph.add_node("b")
    c = graph.add_node("C")
    d = graph.add_node("d")
    e = graph.add_node("e")
    f = graph.add_node("f")
    g = graph.add_node("G")

    graph.add_edge(a, b, None)
    graph.add_edge(a, c, None)
    graph.add_edge(a, d, None)
    graph.add_edge(b, e, None)
    graph.add_edge(c, f, None)
    graph.add_edge(d, g, None)

    expected = [[0], [3, 1], [2], [6], [5, 4]]
    assert list(cluster_compatible_nodes(graph, compare_fn)) == expected


def test_disconnected_components():
    """Test that we get the right clusters when the graph is disconnected."""

    def compare_fn(graph, node_a_idx, node_b_idx):
        """True if the two nodes are both capitalized or not, False otherwise."""
        return graph[node_a_idx].isupper() == graph[node_b_idx].isupper()

    graph = PyDiGraph()
    a = graph.add_node("a")
    b = graph.add_node("b")
    c = graph.add_node("C")
    d = graph.add_node("d")
    e = graph.add_node("e")
    f = graph.add_node("f")
    g = graph.add_node("G")

    graph.add_edge(a, b, None)
    graph.add_edge(a, c, None)
    graph.add_edge(a, d, None)
    graph.add_edge(e, f, None)
    graph.add_edge(e, g, None)

    expected = [[0, 4], [3, 1, 5], [2, 6]]
    assert list(cluster_compatible_nodes(graph, compare_fn)) == expected
