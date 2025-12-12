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

"""BasisChange Serializers"""

import orjson

from ..annotations import VirtualType
from ..exceptions import DeserializationError, SerializationError
from ..samplex.nodes.change_basis_node import BasisChange
from ..utils.serialization import array_from_json, array_to_json
from ..virtual_registers import PauliRegister, U2Register, VirtualRegister, Z2Register
from .type_serializer import DataSerializer, TypeSerializer


def _virtual_register_from_json(data: dict[str, str]) -> VirtualRegister:
    register_type = VirtualType(data["type"])
    array = array_from_json(data["array"])
    if register_type == VirtualType.U2:
        return U2Register(array)
    elif register_type == VirtualType.Z2:
        return Z2Register(array)
    elif register_type == VirtualType.PAULI:
        return PauliRegister(array)
    else:
        raise DeserializationError(f"Invalid register type: {register_type}")


class BasisChangeSerializer(TypeSerializer[BasisChange]):
    """Serializer for :class:`~.BasisChange`."""

    TYPE_ID = "B0"
    TYPE = BasisChange

    class SSV1(DataSerializer[BasisChange]):
        MIN_SSV = 1
        MAX_SSV = 1

        @classmethod
        def serialize(cls, obj, ssv):
            return {
                "alphabet": obj.alphabet,
                "action": orjson.dumps(
                    {"type": obj.action.TYPE, "array": array_to_json(obj.action.virtual_gates)}
                ).decode("utf-8"),
            }

        @classmethod
        def deserialize(cls, data):
            return BasisChange(
                data["alphabet"],
                _virtual_register_from_json(orjson.loads(data["action"])),
            )

    class SSV2(DataSerializer[BasisChange]):
        MIN_SSV = 2

        @classmethod
        def serialize(cls, obj, ssv):
            try:
                type_id = TypeSerializer.TYPE_REGISTRY[(reg_type := type(obj.action))]
            except KeyError:
                raise SerializationError(f"Cannot serialize virtual register of type {reg_type}.")
            action = TypeSerializer.TYPE_ID_REGISTRY[type_id].serialize(obj.action, ssv)
            return {
                "alphabet": obj.alphabet,
                "action": orjson.dumps(action).decode("utf-8"),
            }

        @classmethod
        def deserialize(cls, data):
            return BasisChange(
                data["alphabet"],
                TypeSerializer.deserialize(orjson.loads(data["action"])),
            )
