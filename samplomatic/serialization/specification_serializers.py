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

import numpy as np

from ..tensor_interface import PauliLindbladMapSpecification, TensorSpecification
from .type_serializer import DataSerializer, TypeSerializer


class PauliLindbladMapSpecificationSerializer(TypeSerializer[PauliLindbladMapSpecification]):
    """Serializer for :class:`~.PauliLindbladMapSpecification`."""

    TYPE_ID = "S0"

    class SSV1(DataSerializer[PauliLindbladMapSpecification]):
        MIN_SSV = 1

        @classmethod
        def serialize(cls, obj):
            return {
                "name": obj.name,
                "num_qubits": obj.num_qubits,
                "num_terms": obj.num_terms,
            }

        @classmethod
        def deserialize(cls, data):
            return PauliLindbladMapSpecification(
                data["name"], data["num_qubits"], data["num_terms"]
            )


class TensorSpecificationSerializer(TypeSerializer[TensorSpecification]):
    """Serializer for :class:`~.TensorSpecification`."""

    TYPE_ID = "S1"

    class SSV1(DataSerializer[TensorSpecification]):
        MIN_SSV = 1

        @classmethod
        def serialize(cls, obj):
            return {
                "name": obj.name,
                "description": obj.description,
                "dtype": str(obj.dtype),
                "shape": obj.shape,
                "broadcastable": obj.broadcastable,
                "optional": obj.optional,
            }

        @classmethod
        def deserialize(cls, data):
            return TensorSpecification(
                data["name"],
                tuple(data["shape"]),
                np.dtype(data["dtype"]),
                data["description"],
                data["broadcastable"],
                data["optional"],
            )
