# This code is a Qiskit project.
#
# (C) Copyright IBM 2025-2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Samplex serialization implementation.

See :mod:`samplomatic.serialization` for user-facing documentation.

Maintainer notes on SSV changes
-------------------------------

Serializable types inherit from :class:`~.Serializable` and can be added, removed, or modified
between package versions. The rules for updating the SSV are:

- **Adding a type**: increment the SSV and provide serialization support. Prior SSVs will raise
  an incompatibility error if they encounter the new type.
- **Removing a type**: increment the SSV. Subsequent SSVs will raise backwards-compatibility
  errors when asked to serialize the removed type.
- **Modifying a type**:

  - *Breaking change*: treat as a simultaneous removal and addition. The serialization format may
    change arbitrarily, but the type id **must** change.
  - *Backwards-compatible change*: increment the SSV if the serialization format changed, update
    the :class:`~.DataSerializer` for older SSVs, and implement a new one for the new SSV.
"""

from typing import TypedDict, cast, overload

import orjson
from rustworkx import PyDiGraph, node_link_json, parse_node_link_json

from .._version import version as samplomatic_version
from ..exceptions import SerializationError
from ..samplex import Samplex
from ..samplex.nodes import Node
from ..ssv import SSV
from .node_serializers import *  # noqa: F403
from .parameter_expression_serializer import ParameterExpressionTableSerializer
from .specification_serializers import deserialize_specifications, serialize_specifications
from .type_serializer import TypeSerializer
from .virtual_register_serializers import *  # noqa: F403


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

    def from_samplex(samplex: Samplex, ssv: int = SSV):
        return HeaderV1(
            ssv=str(ssv),
            samplomatic_version=samplomatic_version,
            param_table=orjson.dumps(
                ParameterExpressionTableSerializer.serialize(samplex._param_table, ssv=ssv)  # noqa: SLF001
            ).decode("utf-8"),
            input_specification=serialize_specifications(samplex._input_specifications, ssv=ssv),  # noqa: SLF001
            output_specification=serialize_specifications(samplex._output_specifications, ssv=ssv),  # noqa: SLF001
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


def samplex_to_json(samplex, filename=None, ssv=SSV):
    """Dump a samplex to json.

    Args:
        filename: An optional path to write the json to.
        ssv: The samplex serialization to write.

    Returns:
        Either the json as a string or ``None`` if ``filename`` is specified.

    Raises:
        SerializationError: If ``ssv`` is incompatible.
    """
    header = HeaderV1.from_samplex(samplex, ssv=ssv)

    def serialize_node(node: Node):
        try:
            type_id = TypeSerializer.TYPE_REGISTRY[type(node)]
        except KeyError as exc:
            raise SerializationError(f"Node type {type(node)} cannot be serialized.") from exc
        return TypeSerializer.TYPE_ID_REGISTRY[type_id].serialize(node, ssv)

    return node_link_json(
        samplex.graph,
        path=filename,
        graph_attrs=lambda _: header,
        node_attrs=serialize_node,
    )


def _samplex_from_graph(samplex_graph: PyDiGraph) -> Samplex:
    samplex = Samplex()
    samplex.graph = samplex_graph

    data = cast(HeaderV1, samplex_graph.attrs)
    samplex._param_table = ParameterExpressionTableSerializer.deserialize(  # noqa: SLF001
        orjson.loads(data["param_table"])
    )
    samplex._input_specifications = deserialize_specifications(data["input_specification"])  # noqa: SLF001
    samplex._output_specifications = deserialize_specifications(data["output_specification"])  # noqa: SLF001
    samplex._passthrough_params = deserialize_passthrough_params(data["passthrough_params"])  # noqa: SLF001

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
