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

"""plot_graph"""

from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from typing import TYPE_CHECKING, TypeVar

import numpy as np
from rustworkx import spring_layout
from rustworkx.rustworkx import PyDiGraph, weakly_connected_components

from ..aliases import EdgeLayout, GraphLayout, LayoutMethod, LayoutPresets, NodeLayout, NodeRanker
from ..optionals import HAS_GRAPHVIZ, HAS_NBFORMAT, HAS_PLOTLY
from .graphviz_layout import graphviz_layout
from .hover_style import HoverStyle, NodeStyle

if TYPE_CHECKING:
    from plotly.graph_objects import Figure

COLOR_EDGES: str = "tomato"
ARROW_POS: float = 0.7
ARROW_SIZE: int = 20


T = TypeVar("T")
S = TypeVar("S")


def _auto_layout_method(
    graph: PyDiGraph[T, S], ranker: NodeRanker[T] | None = None
) -> LayoutMethod[T, S]:
    if HAS_GRAPHVIZ:
        return LAYOUT_METHODS["graphviz"](graph, ranker)
    return LAYOUT_METHODS["spring"](graph, ranker)


LAYOUT_METHODS: dict[str, LayoutMethod] = {
    "auto": _auto_layout_method,
    "spring": lambda graph, _: spring_layout(graph, repulsive_exponent=3),
    "graphviz": partial(graphviz_layout, layout="dot", spline="spline"),
    "graphviz_curved": partial(graphviz_layout, layout="dot", spline="curved"),
    "graphviz_line": partial(graphviz_layout, layout="dot", spline="line"),
}


def _add_edge_layout(graph: PyDiGraph, layout: GraphLayout) -> tuple[NodeLayout, EdgeLayout]:
    r"""Add an edge layout to :class:`GraphLayout`\s that only has a node layout."""
    if isinstance(layout, tuple):
        return layout

    node_layout = layout

    edge_layout = {}
    # insert one coordinate that is a mid point. this is where the arrow will go.
    for edge_idx, (node_a, node_b, _) in graph.edge_index_map().items():
        xa, ya = node_layout[node_a]
        xb, yb = node_layout[node_b]
        edge_layout[edge_idx] = np.array([[xa + ARROW_POS * (xb - xa), ya + ARROW_POS * (yb - ya)]])

    return node_layout, edge_layout


@HAS_NBFORMAT.require_in_call
@HAS_PLOTLY.require_in_call
def plot_graph(
    graph: PyDiGraph[T, S],
    cols: int = 2,
    subgraph_idxs: None | int | Sequence[int] = None,
    layout_method: LayoutPresets | LayoutMethod[T, S] = "auto",
    ranker: NodeRanker[T] | None = None,
) -> Figure:
    """Visualize the disconnected subgraphs of a graph.

    This function identifies all disconnected subgraphs within the given ``graph`` using
    the :meth:`~.weakly_connected_components` method. Then, it plots all of the subgraphs
    corresponding to the indices specified in ``subgraph_idxs``, with each selected subgraph
    displayed in its own subplot.

    Args:
        graph: The graph to visualize.
        cols: The number of columns in the returned figure.
        subgraph_idxs: The indices of the connected subgraphs to include in the plot,
            or ``None`` to include all of the available subgraphs.
        layout_method: A predefined layout method by name, or a callable implementing a layout.
        ranker: Specifies a node ranking that can be used by layout methods that group nodes
            topologically.

    Returns:
        A Plotly graph.
    """
    import plotly.graph_objects as go  # pylint: disable=import-outside-toplevel
    from plotly.subplots import make_subplots  # pylint: disable=import-outside-toplevel

    if isinstance(layout_method, str):
        layout_method = LAYOUT_METHODS[layout_method]

    # get the connected components of the input graph
    subgraphs_node_idxs = weakly_connected_components(graph)

    # filter unwanted subgraphs
    if subgraph_idxs is not None:
        if isinstance(subgraph_idxs, int):
            subgraph_idxs = [subgraph_idxs]
        try:
            subgraphs_node_idxs = [subgraphs_node_idxs[i] for i in subgraph_idxs]
        except IndexError as exc:
            raise ValueError(
                f"Cannot plot subgraphs {subgraph_idxs} for a graph with only "
                f"{len(subgraphs_node_idxs)} disconnected components."
            ) from exc

    # initialize the figure
    num_figs = len(subgraphs_node_idxs)
    cols = max(min(num_figs, cols), 1)
    rows = (num_figs // cols + num_figs % cols) or 1
    fig = make_subplots(rows=rows, cols=cols)

    # draw the subgraphs
    for subgraph_idx, subgraph_node_idxs in enumerate(subgraphs_node_idxs):
        subgraph = graph.subgraph(list(subgraph_node_idxs))
        nodes = subgraph.nodes()

        layout = layout_method(subgraph, ranker)
        node_layout, raw_edge_coords = _add_edge_layout(subgraph, layout)

        # Coordinates of nodes, shape (num_nodes, 2), last axis for (x, y)
        node_coords = np.asarray([node_layout[node_idx] for node_idx in subgraph.node_indices()])

        # each edge coord array stores the _intermediate_ coords of the edge. so the total length
        # of the list needs two more for the endpoints of each edge (taken from node_layout) and
        # an extra to act as a delimiter between line segments
        num_edge_coords = sum(3 + coords.shape[0] for coords in raw_edge_coords.values())
        edge_coords = np.empty((num_edge_coords, 2))

        pos = 0
        edge_hovertexts = []
        edge_marker_sizes = []
        edge_marker_symbols = []
        for edge_idx, coords in raw_edge_coords.items():
            edge = subgraph.get_edge_data_by_index(edge_idx)
            node_a, node_b = subgraph.get_edge_endpoints_by_index(edge_idx)
            num_intermediate = coords.shape[0]
            edge_coords[pos, :] = node_coords[node_a]
            edge_coords[pos + 1 : pos + num_intermediate + 1, :] = coords
            edge_coords[pos + num_intermediate + 1, :] = node_coords[node_b]
            edge_coords[pos + num_intermediate + 2, :] = np.nan
            pos += num_intermediate + 3

            mid_point_idx = int(num_intermediate * ARROW_POS) + 1

            edge_hovertexts.extend(
                HoverStyle.from_object(edge).html if idx == mid_point_idx else None
                for idx in range(num_intermediate + 3)
            )
            edge_marker_sizes.extend(
                ARROW_SIZE if idx == mid_point_idx else 0 for idx in range(num_intermediate + 3)
            )
            edge_marker_symbols.extend(
                "arrow" if idx == mid_point_idx else "circle" for idx in range(num_intermediate + 3)
            )

        traces = []
        if edge_coords.size:
            # add edges
            traces.append(
                go.Scatter(
                    x=edge_coords[:, 0],
                    y=edge_coords[:, 1],
                    line=dict(color=COLOR_EDGES, shape="spline", smoothing=1.0),
                    hoverinfo="text",
                    hovertext=edge_hovertexts,
                    mode="lines+markers",
                    marker=dict(
                        size=edge_marker_sizes,
                        symbol=edge_marker_symbols,
                        angleref="previous",
                    ),
                )
            )

        node_hovertexts = []
        node_colors = []
        node_sizes = []
        node_marker_symbols = []
        for style in map(NodeStyle.from_object, nodes):
            node_hovertexts.append(style.html)
            node_marker_symbols.append(style.marker)
            node_colors.append(style.color)
            node_sizes.append(style.size)

        # add nodes
        traces.append(
            go.Scatter(
                x=node_coords[:, 0],
                y=node_coords[:, 1],
                mode="markers+text",
                text=list(subgraph_node_idxs),
                marker=dict(size=node_sizes, color=node_colors, symbol=node_marker_symbols),
                hoverinfo="text",
                hovertext=node_hovertexts,
                hoverlabel=dict(
                    bgcolor="lightyellow", font=dict(family="Times New Roman", color="black")
                ),
            )
        )

        num_traces = len(traces)
        fig.add_traces(
            traces,
            rows=[1 + subgraph_idx // cols] * num_traces,
            cols=[1 + subgraph_idx % cols] * num_traces,
        )

    fig.update_layout(
        showlegend=False,
        margin=dict(l=5, r=5, t=5, b=5),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="white",
    )
    fig.update_xaxes(
        showticklabels=False,
        showgrid=False,
        showline=True,
        linewidth=1,
        linecolor="black",
        mirror=True,
        zeroline=False,
    )
    fig.update_yaxes(
        showticklabels=False,
        showgrid=False,
        showline=True,
        linewidth=1,
        linecolor="black",
        mirror=True,
        zeroline=False,
    )

    return fig
