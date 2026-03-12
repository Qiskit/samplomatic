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

import numpy as np
import orjson
import pytest

from samplomatic.distributions import (
    BalancedUniformPauli,
    HaarU2,
    UniformC1,
    UniformLocalC1,
    UniformPauli,
    UniformPauliSubset,
)
from samplomatic.serialization.distribution_serializers import (
    BalancedUniformPauliSerializer,
    HaarU2Serializer,
    UniformC1Serializer,
    UniformLocalC1Serializer,
    UniformPauliSerializer,
    UniformPauliSubsetSerializer,
)
from samplomatic.serialization.type_serializer import TypeSerializer


@pytest.mark.parametrize("ssv", UniformPauliSerializer.SSVS)
def test_pauli_distribution_serializer_round_trip(ssv):
    distribution = UniformPauli(13)
    data = UniformPauliSerializer.serialize(distribution, ssv)
    orjson.dumps(data)
    assert distribution == TypeSerializer.deserialize(data)


@pytest.mark.parametrize("ssv", HaarU2Serializer.SSVS)
def test_haar_u2_serializer_round_trip(ssv):
    distribution = HaarU2(13)
    data = HaarU2Serializer.serialize(distribution, ssv)
    orjson.dumps(data)
    assert distribution == TypeSerializer.deserialize(data)


@pytest.mark.parametrize("ssv", UniformC1Serializer.SSVS)
def test_c1_distribution_serializer_round_trip(ssv):
    distribution = UniformC1(13)
    data = UniformC1Serializer.serialize(distribution, ssv)
    orjson.dumps(data)
    assert distribution == TypeSerializer.deserialize(data)


@pytest.mark.parametrize("ssv", BalancedUniformPauliSerializer.SSVS)
def test_balanced_pauli_distribution_serializer_round_trip(ssv):
    distribution = BalancedUniformPauli(13)
    data = BalancedUniformPauliSerializer.serialize(distribution, ssv)
    orjson.dumps(data)
    assert distribution == TypeSerializer.deserialize(data)


@pytest.mark.parametrize("ssv", UniformLocalC1Serializer.SSVS)
def test_local_c1_distribution_serializer_round_trip(ssv):
    distribution = UniformLocalC1(12, "cx")
    data = UniformLocalC1Serializer.serialize(distribution, ssv)
    orjson.dumps(data)
    assert distribution == TypeSerializer.deserialize(data)


@pytest.mark.parametrize("ssv", UniformPauliSubsetSerializer.SSVS)
def test_pauli_subset_distribution_serializer_round_trip(ssv):
    distribution = UniformPauliSubset(12, np.array([[0, 1, 2, 3]]))
    data = UniformPauliSubsetSerializer.serialize(distribution, ssv)
    orjson.dumps(data)
    assert distribution == TypeSerializer.deserialize(data)
