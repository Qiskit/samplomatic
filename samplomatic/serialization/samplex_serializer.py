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
Every serialized :class:`~.Samplex` starting with ``samplomatic==0.12.0`` encodes a single-integer
Samplex Serialization Version (SSV).
SSVs are incremented independently of the package version, and the minimum version is tied to the
serialization types and samplex content interplay.
For any particular package version :const:`~SSV` is the latest SSV known about and future versions
can not be loaded.

Seralizable types need to inherit from the :class:`~.Serializable` metaclass. They can be added,
removed, or have modified behavior between package versions. To account for this,

 - If a package version introduces a serializable type, it must increment the SSV and provide
   serialization support for it. Prior SSVs will not be able to serialize samplexes containing this
   type, and an incompatability error will be raised. Future SSVs will be able to save and load the
   new type, unless support is dropped.
 - If a package version removes a serializable type, it must increment the SSV, and trying to
   serialize objects of the given type will raise backwars compatibility errors for subsequent SSVs.
 - If a package modifies the behavior of a serializable type:
   - If there is a fundamental change to behavior, then this will be treated as a simultaneous
     removal of a node type, according to the bullets above, but where the name happens to be the
     same. The serialization format can change arbitrarily, but the node type id _must_ change.
   - If the change to behavior is backwards compatible, it must increment the SSV if the
     serialization format has changed, update the :class:`~.DataSerializer` for older SSVs,
     and implement a new :class:`~.DataSerializer` for the new SSV.
"""

from __future__ import annotations

from typing import TypedDict, cast, overload

import orjson
from rustworkx import PyDiGraph, node_link_json, parse_node_link_json

from .._version import version as samplomatic_version
from ..exceptions import SerializationError
from ..samplex import Samplex
from ..samplex.nodes import (
    Node,
)
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
    header = HeaderV1.from_samplex(samplex)

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
