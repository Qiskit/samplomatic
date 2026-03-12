# This code is a Qiskit project.
#
# (C) Copyright IBM 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Distribution Serializers"""

from ..distributions import (
    BalancedUniformPauli,
    HaarU2,
    UniformC1,
    UniformLocalC1,
    UniformPauli,
    UniformPauliSubset,
)
from ..utils.serialization import array_from_json, array_to_json
from .type_serializer import DataSerializer, TypeSerializer


class UniformPauliSerializer(TypeSerializer[UniformPauli]):
    """Serializer for :class:`~.UniformPauli`."""

    TYPE_ID = "D0"
    TYPE = UniformPauli

    class SSV3(DataSerializer[UniformPauli]):
        MIN_SSV = 3

        @classmethod
        def serialize(cls, obj, ssv):
            return {"num_subsystems": obj.num_subsystems}

        @classmethod
        def deserialize(cls, data):
            return UniformPauli(data["num_subsystems"])


class HaarU2Serializer(TypeSerializer[HaarU2]):
    """Serializer for :class:`~.HaarU2`."""

    TYPE_ID = "D1"
    TYPE = HaarU2

    class SSV3(DataSerializer[HaarU2]):
        MIN_SSV = 3

        @classmethod
        def serialize(cls, obj, ssv):
            return {"num_subsystems": obj.num_subsystems}

        @classmethod
        def deserialize(cls, data):
            return HaarU2(data["num_subsystems"])


class UniformC1Serializer(TypeSerializer[UniformC1]):
    """Serializer for :class:`~.UniformC1`."""

    TYPE_ID = "D2"
    TYPE = UniformC1

    class SSV3(DataSerializer[UniformC1]):
        MIN_SSV = 3

        @classmethod
        def serialize(cls, obj, ssv):
            return {"num_subsystems": obj.num_subsystems}

        @classmethod
        def deserialize(cls, data):
            return UniformC1(data["num_subsystems"])


class BalancedUniformPauliSerializer(TypeSerializer[BalancedUniformPauli]):
    """Serializer for :class:`~.BalancedUniformPauli`."""

    TYPE_ID = "D3"
    TYPE = BalancedUniformPauli

    class SSV3(DataSerializer[BalancedUniformPauli]):
        MIN_SSV = 3

        @classmethod
        def serialize(cls, obj, ssv):
            return {"num_subsystems": obj.num_subsystems}

        @classmethod
        def deserialize(cls, data):
            return BalancedUniformPauli(data["num_subsystems"])


class UniformLocalC1Serializer(TypeSerializer[UniformLocalC1]):
    """Serializer for :class:`~.UniformLocalC1`."""

    TYPE_ID = "D4"
    TYPE = UniformLocalC1

    class SSV3(DataSerializer[UniformLocalC1]):
        MIN_SSV = 3

        @classmethod
        def serialize(cls, obj, ssv):
            return {"num_subsystems": obj.num_subsystems, "gate_name": obj.gate_name}

        @classmethod
        def deserialize(cls, data):
            return UniformLocalC1(data["num_subsystems"], data["gate_name"])


class UniformPauliSubsetSerializer(TypeSerializer[UniformPauliSubset]):
    """Serializer for :class:`~.UniformPauliSubset`."""

    TYPE_ID = "D5"
    TYPE = UniformPauliSubset

    class SSV3(DataSerializer[UniformPauliSubset]):
        MIN_SSV = 3

        @classmethod
        def serialize(cls, obj, ssv):
            return {"num_subsystems": obj.num_subsystems, "paulis": array_to_json(obj.paulis)}

        @classmethod
        def deserialize(cls, data):
            return UniformPauliSubset(data["num_subsystems"], array_from_json(data["paulis"]))
