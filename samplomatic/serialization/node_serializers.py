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

"""Node Serializers"""

import orjson

from ..samplex.nodes import (
    ChangeBasisNode,
)
from .basis_change_serializers import BasisChangeSerializer
from .type_serializer import DataSerializer, TypeSerializer


class ChangeBasisNodeSerializer(TypeSerializer[ChangeBasisNode]):
    """Serializer for :class:`~.ChangeBasisNode`."""

    TYPE_ID = "N0"

    class SSV1(DataSerializer[ChangeBasisNode]):
        MIN_SSV = 1

        @classmethod
        def serialize(cls, obj):
            basis_change_ser = BasisChangeSerializer.serialize(obj._basis_change, 1)  # noqa: SLF001
            return {
                "register_name": obj._register_name,  # noqa: SLF001
                "basis_change": orjson.dumps(basis_change_ser).decode("utf-8"),
                "basis_ref": obj._basis_ref,  # noqa: SLF001
                "num_subsystems": str(obj._num_subsystems),  # noqa: SLF001
            }

        @classmethod
        def deserialize(cls, data):
            return ChangeBasisNode(
                data["register_name"],
                BasisChangeSerializer.deserialize(orjson.loads(data["basis_change"])),
                data["basis_ref"],
                int(data["num_subsystems"]),
            )
