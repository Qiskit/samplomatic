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

from samplomatic.distributions import HaarU2
from samplomatic.serialization.type_serializer import TypeSerializer
from samplomatic.serialization.virtual_register_serializers import (
    PauliRegisterSerializer,
    U2RegisterSerializer,
    Z2RegisterSerializer,
)
from samplomatic.virtual_registers import PauliRegister, Z2Register


@pytest.mark.parametrize("ssv", PauliRegisterSerializer.SSVS)
def test_pauli_register_serializer_round_trip(ssv):
    register = PauliRegister(np.array([0, 1, 2], dtype=np.uint8).reshape(1, 3))
    data = PauliRegisterSerializer.serialize(register, ssv)
    orjson.dumps(data)
    assert register == TypeSerializer.deserialize(data)


@pytest.mark.parametrize("ssv", U2RegisterSerializer.SSVS)
def test_u2_register_serializer_round_trip(ssv, rng):
    register = HaarU2(5).sample(7, rng)
    data = U2RegisterSerializer.serialize(register, ssv)
    orjson.dumps(data)
    assert register == TypeSerializer.deserialize(data)


@pytest.mark.parametrize("ssv", Z2RegisterSerializer.SSVS)
def test_z2_register_serializer_round_trip(ssv):
    register = Z2Register(np.array([[0, 0, 1], [1, 0, 1]], dtype=np.uint8))
    data = Z2RegisterSerializer.serialize(register, ssv)
    orjson.dumps(data)
    assert register == TypeSerializer.deserialize(data)
