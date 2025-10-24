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


"""Samplex serialization

:class:`~.Samplex` objects are serializable and deserializable via :func:`~.samplex_to_json` and
:func:`~.samplex_from_json`.
Since the data structure of a samplex is primarily node-based, a JSON node-link format is used.
All elements of the samplex data model that are not contained directly in the graph itself are
encoded in the graph attributes section of the format. Details about the nodes, such as what type
of :class:`~.Node` they represent, are stored in the corresponding node attributes. Samplexes
have no edge attributes.

Serialization and deserializaiton is performed by :func:`rustworkx.node_link_json` and
:func:`rustworkx.parse_node_link_json`, with attribute dictionaries supplied and defined
by samplomatic.

Versioning
----------

Some backwards compatibility of the serialization format is offered.
Every serialized :class:`~.Samplex` starting with ``samplomatic==0.11.0`` encodes a single-integer
Samplex Serialization Version (SSV).
SSVs are incremented independently of the package version, and every package version describes the
SSV range it is willing to read and write.
For any particular package version:

 - :const:`~SSV` is the latest SSV known about and future versions can not be loaded.
 - :const:`~SSV_MIN_SUPPORTED` is the oldest SSV supported for reading and writing.

Nodes can be added, removed, or have modified behaviour between package versions. To account for
this,

 - If a package version introduces a :class:`~.Node` type, it must increment the SSV and provide
   serialization
   support for it. Prior SSVs will not be able to serialize samplexes containing this node, and
   an incompatability error will be raised. Future SSVs will be able to save and load the new type,
   unless support is dropped.
 - If a package version removes a :class:`~.Node` type, it must increment the SSV, and the
 - If a package modifies the behaviour of a :class:`~.Node` type:
   - If there is a fundamental change to behaviour, then this will be treated as a simultaneous
     removal of a node type, according to the bullets above, but where the name happens to be the
     same. The serialization format can change arbitrarily, but the node type index _must_ change.
   - If the change to behaviour is backwards compatible
"""

from __future__ import annotations

import io
import uuid
from typing import TypedDict, cast, overload

import orjson
import pybase64

# This is super private in Qiskit and on every upgrade should be checked for changes
from qiskit.qpy.binary_io.value import _read_parameter_expr_v13, _write_parameter_expression_v13
from rustworkx import PyDiGraph, node_link_json, parse_node_link_json

from .._version import version as samplomatic_version
from ..aliases import InterfaceName, Parameter, ParameterExpression
from ..exceptions import DeserializationError
from ..tensor_interface import Specification
from .nodes import Node
from .nodes.change_basis_node import ChangeBasisNode
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

__all__ = ["SSV", "SSV_MIN_SUPPORTED", "samplex_from_json", "samplex_to_json"]

SSV = 1
"""The most recent samplex serialization version, and the default version serialized to."""

SSV_MIN_SUPPORTED = 1
"""The minimum samplex serialization version supported by this samplomatic version."""

NODE_TYPE_MAP: list[Node | None] = [
    ChangeBasisNode,
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
"""Serializable node types.

Each node in this list must declare the ``"node_type"`` of its json encoding consistently with its
0-indexed position in this list. For example, ``CombineRegistersNode`` must declare
``"node_type": "3"``. For this reason, once a type is in a position, it must never be moved. If a
node type is removed, it should be replaced by ``None`` to preserve ordering of the other node
types. This list can be extended with new types.
"""


class Header(TypedDict):
    """Template all headers must specify.

    Multiple SSVs can use the same header type.
    """

    ssv: str
    samplomatic_version: str


class HeaderV1(Header):
    param_table: str
    input_specification: str
    output_specification: str
    passthrough_params: str

    def from_samplex(samplex: Samplex):
        return HeaderV1(
            ssv=str(SSV),
            samplomatic_version=samplomatic_version,
            param_table=_serialize_expression_table(samplex._param_table),  # noqa: SLF001
            input_specification=_serialize_specifications(samplex._input_specifications),  # noqa: SLF001
            output_specification=_serialize_specifications(samplex._output_specifications),  # noqa: SLF001
            passthrough_params=_serialize_passthrough_params(samplex._passthrough_params),  # noqa: SLF001
        )


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


def _deserialize_node(node_data: dict[str, str]) -> Node:
    if (node_type := NODE_TYPE_MAP[int(node_data["node_type"])]) is None:
        raise
    return node_type._from_json_dict(node_data)  # noqa: SLF001


@overload
def samplex_to_json(samplex: Samplex, filename: str, ssv: int) -> None: ...


@overload
def samplex_to_json(samplex: Samplex, filename: None, ssv: int) -> str: ...


def samplex_to_json(samplex, filename, ssv=SSV):
    """Dump a samplex to json.

    Args:
        filename: An optional path to write the json to.
        ssv: The samplex serialization to write.

    Returns:
        Either the json as a string or ``None`` if ``filename`` is specified.
    """
    if ssv < SSV_MIN_SUPPORTED:
        raise
    if ssv in {1}:
        header = HeaderV1.from_samplex(samplex)
    else:
        raise

    def serialize_node(node: Node) -> dict[str, str]:
        return node._to_json_dict(ssv)  # noqa: SLF001

    return node_link_json(
        samplex.graph,
        path=filename,
        graph_attrs=lambda _: header,
        node_attrs=serialize_node,
    )


def _samplex_from_graph(samplex_graph: PyDiGraph) -> Samplex:
    ssv = samplex_graph.attrs.get("ssv")
    samplex = Samplex()

    if ssv in {"1"}:
        data = cast(HeaderV1, samplex_graph.attrs)
        samplex._param_table = _deserialize_expression_table(orjson.loads(data["param_table"]))  # noqa: SLF001
        samplex._input_specifications = _deserialize_specifications(data["input_specification"])  # noqa: SLF001
        samplex._output_specifications = _deserialize_specifications(data["output_specification"])  # noqa: SLF001
        samplex._passthrough_params = _deserialize_passthrough_params(data["passthrough_params"])  # noqa: SLF001
    else:
        raise

    samplex_graph.attrs = None
    samplex.graph = samplex_graph
    return samplex


def samplex_from_json(json_data: str) -> Samplex:
    """Load a samplex from a json string.

    Args:
        filename: The json string.

    Returns:
        The loaded samplex.
    """
    samplex_graph = parse_node_link_json(json_data, node_attrs=_deserialize_node)
    return _samplex_from_graph(samplex_graph)
