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

from ..samplex.nodes.change_basis_node import BasisChange
from ..virtual_registers.serialization import virtual_register_from_json
from .type_serializer import DataSerializer, TypeSerializer


class BasisChangeSerializer(TypeSerializer[BasisChange]):
    """Serializer for :class:`~.BasisChange`."""

    TYPE_ID = "B0"
    TYPE = BasisChange

    class SSV1(DataSerializer[BasisChange]):
        MIN_SSV = 1

        @classmethod
        def serialize(cls, obj):
            return {
                "alphabet": obj.alphabet,
                "action": orjson.dumps(obj.action.to_json_dict()).decode("utf-8"),
            }

        @classmethod
        def deserialize(cls, data):
            return BasisChange(
                data["alphabet"],
                virtual_register_from_json(orjson.loads(data["action"])),
            )
