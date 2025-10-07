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

"""Test the plot_graph function"""

import pytest
from rustworkx.rustworkx import PyDiGraph

from samplomatic.optionals import HAS_GRAPHVIZ, HAS_PLOTLY
from samplomatic.visualization.hover_style import EdgeStyle, NodeStyle
from samplomatic.visualization.plot_graph import plot_graph


@pytest.fixture
def disconnected_graph():
    """Graph that we can plot."""
    edge_list = [(3 * i + j, 3 * i + j + 1) for i in range(4) for j in range(2)]
    edge_list.extend([(16, 18), (17, 18), (18, 19)])
    node_list = list(range(max(max(a) for a in edge_list) + 1))

    graph = PyDiGraph()
    graph.add_nodes_from(node_list)
    graph.add_edges_from_no_data(edge_list)

    return graph


@pytest.mark.skipif(not HAS_PLOTLY, reason="plotly is not installed")
class TestPlotGraph:
    """Test the plot_graph function"""

    def test_empty_graph(self, save_plot):
        """Test that empty graph is plotted without error"""
        save_plot(plot_graph(PyDiGraph()))

    @pytest.mark.parametrize("add_hover_data", [True, False])
    def test_basic_graph(self, save_plot, add_hover_data, disconnected_graph):
        """Test that a basic graph is plotted without error"""
        if add_hover_data:
            for a, b in disconnected_graph.edge_list():
                disconnected_graph.update_edge(a, b, EdgeStyle(title=f"{a} -> {b}"))
            for node_idx in disconnected_graph.node_indices():
                node_style = (
                    NodeStyle(title=f"Node: {node_idx}")
                    .append_data("Text Data", "Text")
                    .append_list_data("List Data", [0, 1, 2])
                    .append_list_data("Long List Data", [0, 1, 2, 3, 4, 5, 5, 5], max_display=5)
                    .append_divider()
                    .append_dict_data("Dict Data", {"foo": "goo"})
                    .append_dict_data("Long Dict Data", {f"foo{idx}": "goo" for idx in range(5)})
                )
                disconnected_graph[node_idx] = node_style

        save_plot(plot_graph(disconnected_graph))

    @pytest.mark.parametrize("subgraph_idxs", [None, 3, [1, 2]])
    def test_subgraph_idxs(self, save_plot, subgraph_idxs):
        """Test that ``subgraph_idxs`` works as expected."""
        graph = PyDiGraph()
        graph.add_nodes_from(range(10))
        graph.add_edges_from_no_data([(i, i + 1) for i in (0, 2, 4, 6, 8)])

        save_plot(plot_graph(graph, subgraph_idxs=subgraph_idxs))

    def test_subgraph_idxs_error(self):
        """Test the error triggered by an invalid ``subgraph_idxs``."""
        graph = PyDiGraph()
        graph.add_nodes_from(range(10))
        graph.add_edges_from_no_data([(i, i + 1) for i in (0, 2, 4, 6, 8)])

        with pytest.raises(ValueError, match="a graph with only 5 disconnected components"):
            plot_graph(graph, subgraph_idxs=9)

    @pytest.mark.parametrize("layout", ["auto", "graphviz", "spring"])
    def test_layouts(self, layout, save_plot, disconnected_graph):
        """Test all layout methods."""
        if "graphviz" in layout and not HAS_GRAPHVIZ:
            pytest.skip("graphviz is not installed")

        save_plot(plot_graph(disconnected_graph, layout_method=layout))
