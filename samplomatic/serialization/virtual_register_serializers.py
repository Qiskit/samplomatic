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

"""Specification Serializers"""

from ..virtual_registers import PauliRegister, U2Register, Z2Register
from .type_serializer import DataSerializer, TypeSerializer
from .utils import array_from_json, array_to_json


class PauliRegisterSerializer(TypeSerializer[PauliRegister]):
    """Serializer for :class:`~.PauliRegister`."""

    TYPE_ID = "V0"
    TYPE = PauliRegister

    class SSV1(DataSerializer[PauliRegister]):
        MIN_SSV = 1

        @classmethod
        def serialize(cls, obj):
            return {"array": array_to_json(obj._array)}  # noqa: SLF001

        @classmethod
        def deserialize(cls, data):
            return PauliRegister(array_from_json(data["array"]))


class U2RegisterSerializer(TypeSerializer[U2Register]):
    """Serializer for :class:`~.U2Register`."""

    TYPE_ID = "V1"
    TYPE = U2Register

    class SSV1(DataSerializer[U2Register]):
        MIN_SSV = 1

        @classmethod
        def serialize(cls, obj):
            return {"array": array_to_json(obj._array)}  # noqa: SLF001

        @classmethod
        def deserialize(cls, data):
            return U2Register(array_from_json(data["array"]))


class Z2RegisterSerializer(TypeSerializer[Z2Register]):
    """Serializer for :class:`~.Z2Register`."""

    TYPE_ID = "V2"
    TYPE = Z2Register

    class SSV1(DataSerializer[Z2Register]):
        MIN_SSV = 1

        @classmethod
        def serialize(cls, obj):
            return {"array": array_to_json(obj._array)}  # noqa: SLF001

        @classmethod
        def deserialize(cls, data):
            return Z2Register(array_from_json(data["array"]))
