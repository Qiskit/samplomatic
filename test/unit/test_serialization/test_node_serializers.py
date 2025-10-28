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

import orjson
import pytest

from samplomatic.samplex.nodes import (
    ChangeBasisNode,
)
from samplomatic.samplex.nodes.change_basis_node import MEAS_PAULI_BASIS, PREP_PAULI_BASIS
from samplomatic.serialization.node_serializers import (
    ChangeBasisNodeSerializer,
    CollectTemplateValuesSerializer,
    CollectZ2ToOutputNodeSerializer,
    CombineRegistersNodeSerializer,
    ConversionNodeSerializer,
    InjectNoiseNodeSerializer,
    LeftMultiplicationNodeSerializer,
    LeftU2ParametricMultiplicationNodeSerializer,
    PauliPastCliffordNodeSerializer,
    RightMultiplicationNodeSerializer,
    RightU2ParametricMultiplicationNodeSerializer,
    SliceRegisterNodeSerializer,
    TwirlSamplingNodeSerializer,
)
from samplomatic.serialization.type_serializer import TypeSerializer


@pytest.mark.parametrize("basis_change", [MEAS_PAULI_BASIS, PREP_PAULI_BASIS])
@pytest.mark.parametrize("ssv", ChangeBasisNodeSerializer.SSVS)
def test_change_basis_serializer_round_trip(basis_change, ssv):
    node = ChangeBasisNode("x", basis_change, "ref", 6)
    data = ChangeBasisNodeSerializer.serialize(node, ssv)
    orjson.dumps(data)
    assert node == TypeSerializer.deserialize(data)


@pytest.mark.parametrize("ssv", CollectTemplateValuesSerializer.SSVS)
def test_collect_template_values_serializer_round_trip(ssv):
    pass


@pytest.mark.parametrize("ssv", CollectZ2ToOutputNodeSerializer.SSVS)
def test_collect_z2_serializer_round_trip(ssv):
    pass


@pytest.mark.parametrize("ssv", CombineRegistersNodeSerializer.SSVS)
def test_combine_registers_serializer_round_trip(ssv):
    pass


@pytest.mark.parametrize("ssv", ConversionNodeSerializer.SSVS)
def test_conversion_serializer_round_trip(ssv):
    pass


@pytest.mark.parametrize("ssv", InjectNoiseNodeSerializer.SSVS)
def test_inject_noise_serializer_round_trip(ssv):
    pass


@pytest.mark.parametrize("ssv", LeftMultiplicationNodeSerializer.SSVS)
def test_left_multiplication_serializer_round_trip(ssv, rng):
    pass


@pytest.mark.parametrize("ssv", RightMultiplicationNodeSerializer.SSVS)
def test_right_multiplication_serializer_round_trip(ssv, rng):
    pass


@pytest.mark.parametrize("ssv", PauliPastCliffordNodeSerializer.SSVS)
def test_pauli_past_clifford_serializer_round_trip(ssv):
    pass


@pytest.mark.parametrize("ssv", SliceRegisterNodeSerializer.SSVS)
def test_slice_register_serializer_round_trip(ssv):
    pass


@pytest.mark.parametrize("ssv", TwirlSamplingNodeSerializer.SSVS)
def test_twirl_sampling_serializer_round_trip(ssv):
    pass


@pytest.mark.parametrize("ssv", LeftU2ParametricMultiplicationNodeSerializer.SSVS)
def test_left_u2_multiplication_serializer_round_trip(ssv):
    pass


@pytest.mark.parametrize("ssv", RightU2ParametricMultiplicationNodeSerializer.SSVS)
def test_right_u2_multiplication_serializer_round_trip(ssv):
    pass
