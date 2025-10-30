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

"""Samplex Serializer"""

from typing import TypedDict, cast, overload

import orjson
from rustworkx import PyDiGraph, node_link_json, parse_node_link_json

from .._version import version as samplomatic_version
from ..exceptions import SerializationError
from ..samplex import Samplex
from ..samplex.nodes import (
    ChangeBasisNode,
    CollectTemplateValues,
    CollectZ2ToOutputNode,
    CombineRegistersNode,
    ConversionNode,
    InjectNoiseNode,
    LeftMultiplicationNode,
    LeftU2ParametricMultiplicationNode,
    Node,
    PauliPastCliffordNode,
    RightMultiplicationNode,
    RightU2ParametricMultiplicationNode,
    SliceRegisterNode,
    TwirlSamplingNode,
)
from .node_serializers import *  # noqa: F403
from .parameter_expression_serializer import ParameterExpressionTableSerializer
from .specification_serializers import deserialize_specifications, serialize_specifications
from .type_serializer import SSV, TypeSerializer

SSV_MIN_SUPPORTED = SSV
SUPPORTED_SSVS = set(range(SSV_MIN_SUPPORTED, SSV + 1))

NODE_TYPE_MAP: dict[Node, str] = {
    ChangeBasisNode: "N0",
    CollectTemplateValues: "N1",
    CollectZ2ToOutputNode: "N2",
    CombineRegistersNode: "N3",
    ConversionNode: "N4",
    InjectNoiseNode: "N5",
    LeftMultiplicationNode: "N6",
    PauliPastCliffordNode: "N8",
    SliceRegisterNode: "N9",
    TwirlSamplingNode: "N10",
    LeftU2ParametricMultiplicationNode: "N11",
    RightMultiplicationNode: "N7",
    RightU2ParametricMultiplicationNode: "N12",
}
# TODO: Do we want to use a dict like this or add a Serializable class with corresponding TYPE_ID?


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
            param_table=orjson.dumps(
                ParameterExpressionTableSerializer.serialize(samplex._param_table)  # noqa: SLF001
            ).decode("utf-8"),
            input_specification=serialize_specifications(samplex._input_specifications),  # noqa: SLF001
            output_specification=serialize_specifications(samplex._output_specifications),  # noqa: SLF001
            passthrough_params=serialize_passthrough_params(samplex._passthrough_params),  # noqa: SLF001
        )


def serialize_passthrough_params(data: tuple[list[int], list[int]] | None) -> str:
    if data is None:
        return "None"
    return orjson.dumps([data[0], data[1]]).decode("utf-8")


def deserialize_passthrough_params(data: str) -> tuple[list[int], list[int]] | None:
    if data == "None":
        return None
    return tuple(orjson.loads(data))


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

    Raises:
        SerializationError: If ``ssv`` is invalid.
    """
    if ssv < SSV_MIN_SUPPORTED:
        raise SerializationError(
            f"Cannot serialize a samplex to SSV {ssv}. The minimum "
            f"supported version is {SSV_MIN_SUPPORTED}."
        )
    if ssv in SUPPORTED_SSVS:
        header = HeaderV1.from_samplex(samplex)
    else:
        raise SerializationError(f"Cannot serialize a samplex to unsupported SSV {ssv}.")

    def serialize_node(node: Node):
        return TypeSerializer.TYPE_ID_REGISTRY[NODE_TYPE_MAP[type(node)]].serialize(node)

    return node_link_json(
        samplex.graph,
        path=filename,
        graph_attrs=lambda _: header,
        node_attrs=serialize_node,
    )


def _samplex_from_graph(samplex_graph: PyDiGraph) -> Samplex:
    ssv = samplex_graph.attrs.get("ssv")
    samplex = Samplex()
    samplex.graph = samplex_graph

    if int(ssv) in SUPPORTED_SSVS:
        data = cast(HeaderV1, samplex_graph.attrs)
        samplex._param_table = ParameterExpressionTableSerializer.deserialize(  # noqa: SLF001
            orjson.loads(data["param_table"])
        )
        samplex._input_specifications = deserialize_specifications(data["input_specification"])  # noqa: SLF001
        samplex._output_specifications = deserialize_specifications(data["output_specification"])  # noqa: SLF001
        samplex._passthrough_params = deserialize_passthrough_params(data["passthrough_params"])  # noqa: SLF001
    else:
        raise SerializationError(f"Cannot deserialize a samplex with unsupported SSV {ssv}.")

    return samplex


def samplex_from_json(json_data: str) -> Samplex:
    """Load a samplex from a json string.

    Args:
        filename: The json string.

    Returns:
        The loaded samplex.

    Raises:
        SerializationError: If the SSV specified in the json string is unsupported.
    """
    samplex_graph = parse_node_link_json(json_data, node_attrs=TypeSerializer.deserialize)
    return _samplex_from_graph(samplex_graph)
