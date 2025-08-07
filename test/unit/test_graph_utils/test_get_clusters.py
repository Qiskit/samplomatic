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

from samplomatic.graph_utils import get_clusters


def test_empty_graph():
    """Test edge case of an empty graph."""
    graph = PyDiGraph()
    assert not list(get_clusters(graph, lambda _: False))
    assert not list(get_clusters(graph, lambda _: True))


def test_no_nodes_pass_filter():
    """Test that there are no clusters when the filter is always false."""
    graph = PyDiGraph()
    a = graph.add_node("a")
    b = graph.add_node("b")
    graph.add_edge(a, b, None)
    assert not list(get_clusters(graph, lambda x: False))


def test_all_nodes_pass_filter_single_component():
    """Test that everything is in one cluster when the filter is always true."""
    graph = PyDiGraph()
    a = graph.add_node("a")
    b = graph.add_node("b")
    graph.add_edge(a, b, None)
    clusters = list(get_clusters(graph, lambda x: True))
    assert len(clusters) == 1
    assert set(clusters[0]) == {a, b}


def test_disconnected_components():
    """Test that we get two clusters on an actually disconnected graph, when the filter is true."""
    graph = PyDiGraph()
    a = graph.add_node("a")
    b = graph.add_node("b")
    c = graph.add_node("c")
    d = graph.add_node("d")
    graph.add_edge(a, b, None)  # component 1
    graph.add_edge(c, d, None)  # component 2

    clusters = list(get_clusters(graph, lambda x: True))
    assert len(clusters) == 2
    sets = [set(cluster) for cluster in clusters]
    assert {a, b} in sets
    assert {c, d} in sets


def test_mixed_filtering():
    """Test that we get two clusters on an actually disconnected graph, when the filter is true."""
    graph = PyDiGraph()
    graph.add_edge(a := graph.add_node("keep1"), b := graph.add_node("keep2"), None)  # component1
    graph.add_edge(d := graph.add_node("keep3"), e := graph.add_node("keep4"), None)  # component2

    # connect the graph
    c = graph.add_node("drop")
    graph.add_edge(b, c, None)
    graph.add_edge(c, d, None)

    clusters = set(map(frozenset, get_clusters(graph, lambda x: x.startswith("keep"))))
    assert len(clusters) == 2
    assert frozenset({a, b}) in clusters
    assert frozenset({d, e}) in clusters
