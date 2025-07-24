# This code is part of the Samplomatic project.
#
# This is proprietary IBM software for internal use only, do not distribute outside of IBM
# Unauthorized copying of this file is strictly prohibited
#
# (C) Copyright IBM 2025.

"""Samplex"""

import io
import json
import uuid

import pybase64
from qiskit.circuit import Parameter, ParameterExpression

# This is super private in Qiskit and on every upgrade should be checked for changes
from qiskit.qpy.binary_io.value import (
    _read_parameter_expression_v13,
    _write_parameter_expression_v13,
)
from rustworkx import PyDiGraph, from_node_link_json_file, node_link_json, parse_node_link_json

from .nodes.basis_transform_node import BasisTransformNode
from .nodes.collect_template_values import CollectTemplateValues
from .nodes.collect_z2_to_output_node import CollectZ2ToOutputNode
from .nodes.combine_registers_node import CombineRegistersNode
from .nodes.conversion_node import ConversionNode
from .nodes.inject_noise_node import InjectNoiseNode
from .nodes.multiplication_node import MultiplicationNode
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
    MultiplicationNode,
    PauliPastCliffordNode,
    SliceRegisterNode,
    TwirlSamplingNode,
    U2ParametricMultiplicationNode
]


def _serialize_expressions(expr: ParameterExpression):
    with io.BytesIO() as buf:
        _write_parameter_expression_v13(buf, expr, 15)
        return pybase64.encode(buf.getvalue())

def _deserialize_expression(expr: str):
    with io.BytesIO(pybase64.decode(expr)) as buf:
        return _read_parameter_expression_v13(buf, {}, 15)


def _serialize_expression_table(table: ParameterExpressionTable) -> str:
    return json.dumps({
        "expressions": [_serialize_expressions(x) for x in table._expressions],
        "parameters": {name: param.uuid for name, param in table._parameters.items()},
        "sorted": table._sorted,
    })

def _deserialize_expression_table(json_data: dict[str, str]) -> ParameterExpressionTable:
    param_table = ParameterExpressionTable()
    param_table._sorted = json_data["sorted"] == "true"
    parameters = {name: Parameter(name, uuid=uuid.UUID(_uuid)) for name, _uuid in json_data["parameters"]}
    param_table._parameters = parameters
    expressions = [_deserialize_expression(x) for x in json_data["expressions"]]
    param_table._expressions = expressions
    return param_table

def _generate_graph_header(samplex: Samplex) -> dict[str, str]:
    return {
        "finalized": str(samplex._finalized),
        "param_table": _serialize_expression_table(samplex._param_table),
    }

def _process_graph_header(data: dict[str, str]) -> (ParameterExpressionTable, bool):
    raw_param_table_dict = json.loads(data["param_table"])
    param_table = _deserialize_expression_table(raw_param_table_dict)
    return (param_table, data["finalized"] == "true")


def samplex_to_json(samplex: Samplex, filename: str | None = None) -> str | None:
    def node_attr(x):
        return x._to_json_dict()

    return node_link_json(
        samplex.graph,
        path=filename,
        graph_attrs=lambda _: _generate_graph_header(samplex),
        node_attrs=node_attr,
    )

def _samplex_from_graph(samplex_graph: PyDiGraph) -> Samplex:
    graph_attrs = _process_graph_header(samplex_graph.attrs)
    samplex_graph.attrs = None
    samplex = Samplex()
    samplex.graph = samplex_graph
    samplex._param_table = graph_attrs[0]
    samplex._finalized = graph_attrs[1]
    return samplex


def samplex_from_json_file(filename: str) -> Samplex:
    samplex_graph = from_node_link_json_file(filename)
    return _samplex_from_graph(samplex_graph)

def samplex_from_json(json_data: str) -> Samplex:
    samplex_graph = parse_node_link_json(json_data)
    return _samplex_from_graph(samplex_graph)
