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

"""Type Aliases"""

import sys as _sys
from collections.abc import Hashable as _Hashable
from collections.abc import Sequence as _Sequence
from typing import Literal as _Literal
from typing import Protocol as _Protocol
from typing import TypeVar as _TypeVar
from typing import Union as _Union

if _sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

if _sys.version_info >= (3, 11):
    from typing import Self  # noqa: F401
else:
    from typing_extensions import Self  # noqa: F401

import numpy as np
from qiskit.circuit import CircuitInstruction as _CircuitInstruction
from qiskit.circuit import Parameter as _Parameter
from qiskit.circuit import ParameterExpression as _ParameterExpression
from qiskit.circuit import Qubit as _Qubit
from qiskit.dagcircuit import DAGOpNode as _DAGOpNode
from rustworkx.rustworkx import PyDiGraph as _PyDiGraph

T = _TypeVar("T")
S = _TypeVar("S")

# this alias patches a qiskit/pyo3 typing bug, it can be removed when fixed in qiskit
CircuitInstruction: TypeAlias = _CircuitInstruction  #  type: ignore
DAGOpNode: TypeAlias = _DAGOpNode  # type: ignore
Parameter: TypeAlias = _Parameter  #  type: ignore
ParameterExpression: TypeAlias = _ParameterExpression  #  type: ignore
Qubit: TypeAlias = _Qubit  # type:ignore

EdgeIndex: TypeAlias = int
OperationName: TypeAlias = str
OutputIndex: TypeAlias = str
InterfaceName: TypeAlias = str
ParamIndex: TypeAlias = int
ParamIndices: TypeAlias = np.ndarray[tuple[int, int], np.dtype[np.intp]]
ParamName: TypeAlias = str
ParamValues: TypeAlias = _Union[_Sequence[float], dict[Parameter, float]]
ParamSpec: TypeAlias = list[tuple[_Union[ParamIndex, None], ParameterExpression]]
QubitIndex: TypeAlias = int
ClbitIndex: TypeAlias = int
PauliBasisChange: TypeAlias = np.ndarray[tuple[int], np.dtype[np.uint8]]
RegisterName: TypeAlias = str
NodeIndex: TypeAlias = int
NumSubsystems: TypeAlias = int
StrRef: TypeAlias = str
SubsystemIndex: TypeAlias = int
SubsystemIndices: TypeAlias = np.ndarray[tuple[int], np.dtype[np.intp]]

NodeLayout: TypeAlias = dict[NodeIndex, tuple[float, float]]
"""A map from graph node indices to :math:`(x, y)` coordinates."""

EdgeLayout: TypeAlias = dict[EdgeIndex, np.ndarray[tuple[int, 2], np.dtype[float]]]
"""A map from graph edge indices to coordinate arrays specifying a curved path.

The arrays need to have at least one entry so that there is somewhere to put the edge's arrow.
The arrays need not include the end-points; those are inferred from a node layout.
"""

GraphLayout: TypeAlias = _Union[NodeLayout, tuple[NodeLayout, EdgeLayout]]
"""A node layout, or a node layout and an edge layout.

The graph plotter will infer linear edges in the former case.
"""


class NodeRanker(_Protocol[T]):
    """Specifies a node ranking that can be used by layout methods to group nodes topologically.

    A return value of ``None`` signifies no rank specified.
    """

    def __call__(self, node: T) -> _Hashable: ...


class LayoutMethod(_Protocol[T, S]):
    """A callable that accepts a graph and returns a coordinate layout."""

    def __call__(
        self, graph: _PyDiGraph[T, S], ranker: _Union[NodeRanker[T], None] = None
    ) -> GraphLayout: ...


LayoutPresets: TypeAlias = _Literal[
    "auto",
    "spring",
    "graphviz",
    "graphviz_curved",
    "graphviz_line",
]
"""Preset layout methods for graph plotting.

 * ``'auto'``: Use some graphviz method if installed, use ``'spring'`` otherwise.
 * ``'graphviz'``: Use graphviz with dot and splined edges.
 * ``'graphviz_curved'``: Use graphviz with dot and curved edges.
 * ``'graphviz_line'``: Use graphviz with dot and straight edges.
 * ``'spring'``: Use the :mod:`rustworkx` spring layout method.
"""
