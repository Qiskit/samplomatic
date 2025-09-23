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


"""Samplex serialization"""

from __future__ import annotations

import io
import uuid

import orjson
import pybase64

# This is super private in Qiskit and on every upgrade should be checked for changes
from qiskit.qpy.binary_io.value import _read_parameter_expr_v13, _write_parameter_expression_v13
from rustworkx import PyDiGraph, node_link_json, parse_node_link_json

from ..aliases import InterfaceName, Parameter, ParameterExpression
from ..exceptions import DeserializationError
from ..tensor_interface import Specification, TensorSpecification
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
from .noise_model_requirement import NoiseModelRequirement
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
    for x in table._expressions:  # noqa: SLF001
        if isinstance(x, Parameter):
            expressions.append({"param": (x.uuid.hex, x.name)})
        else:
            expressions.append({"expression": _serialize_expressions(x)})

    return orjson.dumps(expressions).decode("utf-8")


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


def _serialize_specifications(data: dict[InterfaceName, Specification]) -> str:
    out_dict = {}
    for name, spec in data.items():
        out_dict[name] = orjson.dumps(spec._to_json_dict()).decode("utf-8")  # noqa: SLF001
    return orjson.dumps(out_dict).decode("utf-8")


def _deserialize_specifications(data: str) -> dict[InterfaceName, Specification]:
    outputs_raw = orjson.loads(data)
    outputs = {}
    for name, output in outputs_raw.items():
        outputs[name] = Specification._from_json(orjson.loads(output))  # noqa: SLF001
    return outputs


def _serialize_passthrough_params(data: tuple[list[int], list[int]] | None) -> str:
    if data is None:
        return "None"
    return orjson.dumps([data[0], [data[1]]]).decode("utf-8")


def _deserialize_passthrough_params(data: str) -> tuple[list[int], list[int]] | None:
    if data == "None":
        return None
    return tuple(orjson.loads(data))


def _serialize_noise_requirements(data: dict[str, NoiseModelRequirement]) -> str:
    out_dict = {}
    for name, spec in data.items():
        out_dict[name] = orjson.dumps(spec._to_json_dict()).decode("utf-8")  # noqa: SLF001
    return orjson.dumps(out_dict).decode("utf-8")


def _deserialize_noise_requirements(data: str) -> dict[str, NoiseModelRequirement]:
    outputs_raw = orjson.loads(data)
    outputs = {}
    for name, output in outputs_raw.items():
        outputs[name] = NoiseModelRequirement._from_json(orjson.loads(output))  # noqa: SLF001
    return outputs


def _generate_graph_header(samplex: Samplex) -> dict[str, str]:
    return {
        "finalized": str(samplex._finalized),  # noqa: SLF001
        "param_table": _serialize_expression_table(samplex._param_table),  # noqa: SLF001
        "input_specification": _serialize_specifications(samplex._input_specifications),  # noqa: SLF001
        "output_specification": _serialize_specifications(samplex._output_specifications),  # noqa: SLF001
        "passthrough_params": _serialize_passthrough_params(samplex._passthrough_params),  # noqa: SLF001
        "noise_requirements": _serialize_noise_requirements(samplex._noise_model_requirements),  # noqa: SLF001
    }


def _process_graph_header(
    data: dict[str, str],
) -> tuple[
    ParameterExpressionTable,
    bool,
    dict[InterfaceName, TensorSpecification],
    dict[InterfaceName, TensorSpecification],
    dict[str, NoiseModelRequirement],
]:
    raw_param_table_dict = orjson.loads(data["param_table"])
    param_table = _deserialize_expression_table(raw_param_table_dict)
    inputs = _deserialize_specifications(data["input_specification"])
    outputs = _deserialize_specifications(data["output_specification"])
    passthrough_params = _deserialize_passthrough_params(data["passthrough_params"])
    noise_requirements = _deserialize_noise_requirements(data["noise_requirements"])
    return (
        param_table,
        data["finalized"] == "true",
        inputs,
        outputs,
        passthrough_params,
        noise_requirements,
    )


def samplex_to_json(samplex: Samplex, filename: str | None = None) -> str | None:
    """Dump a samplex to json.

    Args:
        filename: An optional path to write the json to.

    Returns:
        Either the json as a string or ``None`` if ``filename`` is specified.
    """

    def node_attr(x: Node):
        return x._to_json_dict()  # noqa: SLF001

    return node_link_json(
        samplex.graph,
        path=filename,
        graph_attrs=lambda _: _generate_graph_header(samplex),
        node_attrs=node_attr,
    )


def _parse_node(node_data: dict[str, str]) -> Node:
    node_type_index = int(node_data["node_type"])
    return NODE_TYPE_MAP[node_type_index]._from_json_dict(node_data)  # noqa: SLF001


def _samplex_from_graph(samplex_graph: PyDiGraph) -> Samplex:
    graph_attrs = _process_graph_header(samplex_graph.attrs)
    samplex_graph.attrs = None
    samplex = Samplex()
    samplex.graph = samplex_graph
    samplex._param_table = graph_attrs[0]  # noqa: SLF001
    samplex._finalized = graph_attrs[1]  # noqa: SLF001
    samplex._input_specifications = graph_attrs[2]  # noqa: SLF001
    samplex._output_specifications = graph_attrs[3]  # noqa: SLF001
    samplex._passthrough_params = graph_attrs[4]  # noqa: SLF001
    samplex._noise_model_requirements = graph_attrs[5]  # noqa: SLF001
    return samplex


def samplex_from_json(json_data: str) -> Samplex:
    """Load a samplex from a json string.

    Args:
        filename: The json string.

    Returns:
        The loaded samplex.
    """
    samplex_graph = parse_node_link_json(json_data, node_attrs=_parse_node)
    return _samplex_from_graph(samplex_graph)
