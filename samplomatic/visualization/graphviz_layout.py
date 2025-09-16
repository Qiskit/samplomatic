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

"""graphviz_layout"""

from __future__ import annotations

import subprocess
from collections import defaultdict
from tempfile import NamedTemporaryFile
from typing import Literal, TypeVar

import numpy as np
from rustworkx.rustworkx import PyDiGraph

from ..aliases import EdgeLayout, NodeLayout, NodeRanker
from ..optionals import HAS_GRAPHVIZ

T = TypeVar("T")
S = TypeVar("S")


@HAS_GRAPHVIZ.require_in_call
def graphviz_layout(
    graph: PyDiGraph[T, S],
    ranker: NodeRanker[T] | None,
    layout: Literal["dot", "neato"],
    rankdir: Literal["LR", "RL", "BT"] = "LR",
    spline: Literal["spline", "curved", "line", "polyline", "ortho"] = "spline",
) -> tuple[NodeLayout, EdgeLayout]:
    """Compute layout coordinates using pygraphviz.

    Args:
        graph: A rustworkx :class:`~.PyDiGraph`.
        ranker: A node-ranking callable.
        layout: The layout method to choose.
        rankdir: The direction of the dot layout.
        spline: The available graphviz edge curve algorithm options. See
            `graphviz documentation <https://graphviz.org/docs/attrs/splines/>`_.

    Returns:
        A dict mapping node indices to coordinates.
    """
    # this is a weird implementation where we call out to graphviz as a subprocess on a temporary
    # file describing the graph. however, it's nicer than depending on one of the
    # janky graphviz python libaries.

    ranks = defaultdict(set)
    if ranker is not None:
        for node_idx in graph.node_indices():
            ranks[ranker(graph[node_idx])].add(node_idx)
    ranks.pop(None, None)

    graph_text = ["digraph G {", "    node [shape=circle];", f"    splines={spline};"]
    graph_text.append(f"    rankdir={rankdir};")
    graph_text.extend(f'    {node_idx} [label="{node_idx}"];' for node_idx in graph.node_indices())
    for node_a, node_b in graph.edge_list():
        graph_text.append(f'    {node_a} -> {node_b} [label="{node_a}->{node_b}"];')
    for rank_group in ranks.values():
        graph_text.append(f"    {{ rank=same; {'; '.join(map(str, rank_group))}}}")
    graph_text.append("}")

    with NamedTemporaryFile("w+", suffix=".dot", delete=False) as file:
        file.write("\n".join(graph_text))
        file.flush()
        output = subprocess.check_output([layout, "-Tplain", file.name], encoding="utf-8")

    node_layout = {}
    edge_layout = {}
    for line in output.splitlines():
        parts = line.strip().split()
        if not parts:
            continue
        if parts[0] == "node":
            node_layout[int(parts[1])] = tuple(map(float, parts[2:4]))
        elif parts[0] == "edge":
            tail = int(parts[1])
            head = int(parts[2])
            edge_idx = graph.edge_indices_from_endpoints(tail, head)[0]

            num_points = int(parts[3])

            coords = np.empty((num_points, 2))
            coords[:, 0] = [float(x_coord) for x_coord in parts[4 : 4 + 2 * num_points - 1 : 2]]
            coords[:, 1] = [float(y_coord) for y_coord in parts[5 : 4 + 2 * num_points : 2]]

            edge_layout[edge_idx] = render_bezier_spline(coords)

    return node_layout, edge_layout


def render_bezier_spline(
    control_points: np.ndarray[tuple[int, 2], np.dtype[float]], steps_per_segment: int = 5
) -> np.ndarray[tuple[int, 2], np.dtype[float]]:
    """Render a Bezier spline.

    A Bezier spline is a smooth, curved line defined by two endpoints and a number of
    control points. The curve passes through the endpoints but not necessarily the control
    points, which influence the curve's shape by acting as "pulling" magnets.

    Args:
        control_points: A :math:`(3n+1, 2)` array of coordinates, where each set of 4 points
            ``control_points[3*i: 3*(i+1)+1]`` defines the i'th cubic Bezier control points.
            See `documentation <https://cprimozic.net/notes/posts/graphviz-spline-drawing/>`_.
        steps_per_segment: The number of points to evaluate per segment.

    Returns:
        An array of interpolated spline points.
    """
    num_segments = (len(control_points) - 1) // 3

    if control_points.shape != (num_segments * 3 + 1, 2):
        raise ValueError("Expected the control point array must be of shape (3n+1, 2).")

    # put each set of 4 control points into the second axis
    segments = np.empty((num_segments, 4, 2))
    segments[:, 0, :] = control_points[:-1:3]
    segments[:, 1:, :] = control_points[1:].reshape(num_segments, 3, 2)

    # define the bezier transformation
    steps = np.linspace(0, 1, steps_per_segment, endpoint=True)
    basis = np.stack(
        [
            (1 - steps) ** 3,
            3 * (1 - steps) ** 2 * steps,
            3 * (1 - steps) * steps**2,
            steps**3,
        ],
        axis=1,
    )

    # perform the rendering
    return np.einsum("sf,nfd->nsd", basis, segments).reshape(-1, 2)
