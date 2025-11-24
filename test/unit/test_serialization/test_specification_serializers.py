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

import numpy as np
import orjson
import pytest

from samplomatic.serialization.specification_serializers import (
    PauliLindbladMapSpecificationSerializer,
    TensorSpecificationSerializer,
)
from samplomatic.serialization.type_serializer import TypeSerializer
from samplomatic.tensor_interface import PauliLindbladMapSpecification, TensorSpecification


@pytest.mark.parametrize("ssv", PauliLindbladMapSpecificationSerializer.SSVS)
def test_pauli_lindblad_specification_round_trip(ssv):
    node = PauliLindbladMapSpecification("noise", 17, 23)
    data = PauliLindbladMapSpecificationSerializer.serialize(node, ssv)
    orjson.dumps(data)
    assert node == TypeSerializer.deserialize(data)


@pytest.mark.parametrize("ssv", TensorSpecificationSerializer.SSVS)
def test_tensor_specification_round_trip(ssv):
    node = TensorSpecification("my_array", (3, 7, 13), np.uint32, "it's my array")
    data = TensorSpecificationSerializer.serialize(node, ssv)
    orjson.dumps(data)
    assert node == TypeSerializer.deserialize(data)
