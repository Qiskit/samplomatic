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

from ..exceptions import SerializationError
from ..samplex.nodes.change_basis_node import BasisChange
from .type_serializer import DataSerializer, TypeSerializer


class BasisChangeSerializer(TypeSerializer[BasisChange]):
    """Serializer for :class:`~.BasisChange`."""

    TYPE_ID = "B0"
    TYPE = BasisChange

    class SSV2(DataSerializer[BasisChange]):
        MIN_SSV = 2

        @classmethod
        def serialize(cls, obj):
            try:
                type_id = TypeSerializer.TYPE_REGISTRY[(reg_type := type(obj.action))]
            except KeyError:
                raise SerializationError(f"Cannot serialize virtual register of type {reg_type}.")
            action = TypeSerializer.TYPE_ID_REGISTRY[type_id].serialize(obj.action)
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
