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


"""Samplex"""

import io
import json

import pybase64
from qiskit.circuit import Parameter, ParameterExpression

# This is super private in Qiskit and on every upgrade should be checked for changes
from qiskit.qpy.binary_io.value import (
    _read_parameter_expr_v13,
    _write_parameter_expression_v13,
)
from rustworkx import PyDiGraph, from_node_link_json_file, node_link_json, parse_node_link_json

from .nodes import Node
from .nodes.basis_transform_node import BasisTransformNode
from .nodes.collect_template_values import CollectTemplateValues
from .nodes.collect_z2_to_output_node import CollectZ2ToOutputNode
from .nodes.combine_registers_node import CombineRegistersNode
from .nodes.conversion_node import ConversionNode
from .nodes.inject_noise_node import InjectNoiseNode
from .nodes.multiplication_node import LeftMultiplicationNode, RightMultiplicationNode
from .nodes.pauli_past_clifford_node import PauliPastCliffordNode
from .nodes.slice_register_node import SliceRegisterNode
from .nodes.twirl_sampling_node import TwirlSamplingNode
from .nodes.u2_param_multiplication_node import U2ParametricMultiplicationNode
from .parameter_expression_table import ParameterExpressionTable
from .samplex import Samplex

NODE_TYPE_MAP = [
    BasisTransformNode,
    CollectTemplateValues,
    CollectZ2ToOutputNode,
    CombineRegistersNode,
    ConversionNode,
    InjectNoiseNode,
    LeftMultiplicationNode,
    PauliPastCliffordNode,
    SliceRegisterNode,
    TwirlSamplingNode,
    U2ParametricMultiplicationNode,
    RightMultiplicationNode,
]


def _serialize_expressions(expr: ParameterExpression):
    with io.BytesIO() as buf:
        _write_parameter_expression_v13(buf, expr, 15)
        return pybase64.b64encode_as_string(buf.getvalue()).decode("utf-8")


def _deserialize_expression(expr: str, parameters: dict[str, Parameter]):
    with io.BytesIO(pybase64.b64decode(expr)) as buf:
        return _read_parameter_expr_v13(buf, parameters, 15)


def _serialize_expression_table(table: ParameterExpressionTable) -> str:
    return json.dumps([_serialize_expressions(x) for x in table._expressions])  # noqa: SLF001


def _deserialize_expression_table(json_data: str) -> ParameterExpressionTable:
    param_table = ParameterExpressionTable()
    for expression in map(_deserialize_expression, json_data):
        param_table.append(expression)
    return param_table


def _generate_graph_header(samplex: Samplex) -> dict[str, str]:
    return {
        "finalized": str(samplex._finalized),  # noqa: SLF001
        "param_table": _serialize_expression_table(samplex._param_table),  # noqa: SLF001
    }


def _process_graph_header(data: dict[str, str]) -> tuple[ParameterExpressionTable, bool]:
    raw_param_table_dict = json.loads(data["param_table"])
    param_table = _deserialize_expression_table(raw_param_table_dict)
    return (param_table, data["finalized"] == "true")


def samplex_to_json(samplex: Samplex, filename: str | None = None) -> str | None:
    def node_attr(x: Node):
        return x._to_json_dict()  # noqa: SLF001

    return node_link_json(
        samplex.graph,
        path=filename,
        graph_attrs=lambda _: _generate_graph_header(samplex),
        node_attrs=node_attr,
    )


def parse_node(node_data: dict[str, str]) -> Node:
    node_type_index = int(node_data["node_type"])
    return NODE_TYPE_MAP[node_type_index]._from_json_dict(node_data)


def _samplex_from_graph(samplex_graph: PyDiGraph) -> Samplex:
    graph_attrs = _process_graph_header(samplex_graph.attrs)
    samplex_graph.attrs = None
    samplex = Samplex()
    samplex.graph = samplex_graph
    samplex._param_table = graph_attrs[0]  # noqa: SLF001
    samplex._finalized = graph_attrs[1]  # noqa: SLF001
    return samplex


def samplex_from_json_file(filename: str) -> Samplex:
    samplex_graph = from_node_link_json_file(filename, node_attrs=parse_node)
    return _samplex_from_graph(samplex_graph)


def samplex_from_json(json_data: str) -> Samplex:
    samplex_graph = parse_node_link_json(json_data, node_attrs=parse_node)
    return _samplex_from_graph(samplex_graph)
