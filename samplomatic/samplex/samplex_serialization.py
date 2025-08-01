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
import uuid

import pybase64
from qiskit.circuit import Parameter, ParameterExpression

# This is super private in Qiskit and on every upgrade should be checked for changes
from qiskit.qpy.binary_io.value import (
    _read_parameter_expr_v13,
    _write_parameter_expression_v13,
)
from rustworkx import PyDiGraph, from_node_link_json_file, node_link_json, parse_node_link_json

from ..aliases import OutputName
from ..exceptions import DeserializationError
from . import samplex_output
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
from .nodes.u2_param_multiplication_node import (
    LeftU2ParametricMultiplicationNode,
    RightU2ParametricMultiplicationNode,
)
from .parameter_expression_table import ParameterExpressionTable
from .samplex import Samplex
from .samplex_output import OutputSpecification

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
    LeftU2ParametricMultiplicationNode,
    RightMultiplicationNode,
    RightU2ParametricMultiplicationNode,
]


def _serialize_expressions(expr: ParameterExpression):
    with io.BytesIO() as buf:
        _write_parameter_expression_v13(buf, expr, 15)
        return pybase64.b64encode_as_string(buf.getvalue())


def _deserialize_expression(expr: str, parameters: dict[str, Parameter]):
    with io.BytesIO(pybase64.b64decode(expr)) as buf:
        return _read_parameter_expr_v13(buf, parameters, 15)


def _serialize_expression_table(table: ParameterExpressionTable) -> str:
    expressions = []
    for x in table._expressions:
        if isinstance(x, Parameter):
            expressions.append({"param": (x.uuid.hex, x.name)})
        else:
            expressions.append({"expression": _serialize_expressions(x)})

    return json.dumps(expressions)  # noqa: SLF001


def _deserialize_expression_table(json_data: str) -> ParameterExpressionTable:
    param_table = ParameterExpressionTable()
    for expression in json_data:
        if param := expression.get("param"):
            param_table.append(Parameter(param[1], uuid=uuid.UUID(param[0])))
        elif expr_data := expression.get("expression"):
            param_table.append(_deserialize_expression(expr_data, {}))
        else:
            raise DeserializationError("Invalid parameter in expression table")
    return param_table

def _serialize_output_specifications(data: dict[OutputName, OutputSpecification]) -> str:
    out_dict = {}
    for name, spec in data.items():
        out_dict[name] = {spec.__class__.__name__: spec._to_json()}
    return json.dumps(out_dict)

def _deserialize_output_specifications(data: str) -> dict[OutputName, OutputSpecification]:
    outputs_raw = json.loads(data)
    outputs = {}
    for name, output in outputs_raw.items():
        for cls_name, output_dict in output.items():
            outputs[name] = getattr(samplex_output, cls_name)._from_json(json.loads(output_dict))
    return outputs

def _generate_graph_header(samplex: Samplex) -> dict[str, str]:
    return {
        "finalized": str(samplex._finalized),  # noqa: SLF001
        "param_table": _serialize_expression_table(samplex._param_table),  # noqa: SLF001
        "output_specification": _serialize_output_specifications(samplex._output_specifications)
    }


def _process_graph_header(data: dict[str, str]) -> tuple[ParameterExpressionTable, bool, dict[OutputName, OutputSpecification]]:
    raw_param_table_dict = json.loads(data["param_table"])
    param_table = _deserialize_expression_table(raw_param_table_dict)
    outputs = _deserialize_output_specifications(data["output_specification"])
    return (param_table, data["finalized"] == "true", outputs)


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
    samplex._output_specifications = graph_attrs[2]
    return samplex


def samplex_from_json_file(filename: str) -> Samplex:
    samplex_graph = from_node_link_json_file(filename, node_attrs=parse_node)
    return _samplex_from_graph(samplex_graph)


def samplex_from_json(json_data: str) -> Samplex:
    samplex_graph = parse_node_link_json(json_data, node_attrs=parse_node)
    return _samplex_from_graph(samplex_graph)
