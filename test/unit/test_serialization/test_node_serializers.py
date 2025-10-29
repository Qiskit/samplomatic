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

from samplomatic.annotations import VirtualType
from samplomatic.distributions import UniformPauli
from samplomatic.samplex.nodes import (
    ChangeBasisNode,
    CollectTemplateValues,
    CollectZ2ToOutputNode,
    CombineRegistersNode,
    ConversionNode,
    InjectNoiseNode,
    LeftMultiplicationNode,
    LeftU2ParametricMultiplicationNode,
    PauliPastCliffordNode,
    RightMultiplicationNode,
    RightU2ParametricMultiplicationNode,
    SliceRegisterNode,
    TwirlSamplingNode,
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
from samplomatic.synths import RzSxSynth


@pytest.mark.parametrize("basis_change", [MEAS_PAULI_BASIS, PREP_PAULI_BASIS])
@pytest.mark.parametrize("ssv", ChangeBasisNodeSerializer.SSVS)
def test_change_basis_serializer_round_trip(basis_change, ssv):
    node = ChangeBasisNode("x", basis_change, "ref", 6)
    data = ChangeBasisNodeSerializer.serialize(node, ssv)
    orjson.dumps(data)
    assert node == TypeSerializer.deserialize(data)


@pytest.mark.parametrize("ssv", CollectTemplateValuesSerializer.SSVS)
def test_collect_template_values_serializer_round_trip(ssv):
    node = CollectTemplateValues("values", [[0, 1, 3]], "x", VirtualType.U2, [2], RzSxSynth())
    data = CollectTemplateValuesSerializer.serialize(node, ssv)
    orjson.dumps(data)
    assert node == TypeSerializer.deserialize(data)


@pytest.mark.parametrize("ssv", CollectZ2ToOutputNodeSerializer.SSVS)
def test_collect_z2_serializer_round_trip(ssv):
    node = CollectZ2ToOutputNode("reg", [0, 2], "out", [1, 3])
    data = CollectZ2ToOutputNodeSerializer.serialize(node, ssv)
    orjson.dumps(data)
    assert node == TypeSerializer.deserialize(data)


@pytest.mark.parametrize("ssv", CombineRegistersNodeSerializer.SSVS)
def test_combine_registers_serializer_round_trip(ssv):
    operands = {"reg": [(0, 1), (0, 2), VirtualType.PAULI], "other": [(2,), (1,), VirtualType.U2]}
    node = CombineRegistersNode(VirtualType.U2, "larger_reg", 3, operands)
    data = CombineRegistersNodeSerializer.serialize(node, ssv)
    orjson.dumps(data)
    assert node == TypeSerializer.deserialize(data)


@pytest.mark.parametrize("ssv", ConversionNodeSerializer.SSVS)
def test_conversion_serializer_round_trip(ssv):
    node = ConversionNode("existing", VirtualType.PAULI, "new", VirtualType.U2, 5, True)
    data = ConversionNodeSerializer.serialize(node, ssv)
    orjson.dumps(data)
    assert node == TypeSerializer.deserialize(data)


@pytest.mark.parametrize("ssv", InjectNoiseNodeSerializer.SSVS)
def test_inject_noise_serializer_round_trip(ssv):
    node = InjectNoiseNode("injection", "the_sign", "my_noise", 3)
    data = InjectNoiseNodeSerializer.serialize(node, ssv)
    orjson.dumps(data)
    assert node == TypeSerializer.deserialize(data)


@pytest.mark.parametrize("ssv", LeftMultiplicationNodeSerializer.SSVS)
def test_left_multiplication_serializer_round_trip(ssv, rng):
    node = LeftMultiplicationNode(UniformPauli(5).sample(1, rng), "a")
    data = LeftMultiplicationNodeSerializer.serialize(node, ssv)
    orjson.dumps(data)
    assert node == TypeSerializer.deserialize(data)


@pytest.mark.parametrize("ssv", RightMultiplicationNodeSerializer.SSVS)
def test_right_multiplication_serializer_round_trip(ssv, rng):
    node = RightMultiplicationNode(UniformPauli(5).sample(1, rng), "a")
    data = RightMultiplicationNodeSerializer.serialize(node, ssv)
    orjson.dumps(data)
    assert node == TypeSerializer.deserialize(data)


@pytest.mark.parametrize("ssv", PauliPastCliffordNodeSerializer.SSVS)
def test_pauli_past_clifford_serializer_round_trip(ssv):
    node = PauliPastCliffordNode("cx", "my_reg", [(0, 1), (4, 2)])
    data = PauliPastCliffordNodeSerializer.serialize(node, ssv)
    orjson.dumps(data)
    assert node == TypeSerializer.deserialize(data)


@pytest.mark.parametrize("ssv", SliceRegisterNodeSerializer.SSVS)
def test_slice_register_serializer_round_trip(ssv):
    node = SliceRegisterNode(VirtualType.PAULI, VirtualType.U2, "reg_in", "reg_out", [0, 1])
    data = SliceRegisterNodeSerializer.serialize(node, ssv)
    orjson.dumps(data)
    assert node == TypeSerializer.deserialize(data)


@pytest.mark.parametrize("ssv", TwirlSamplingNodeSerializer.SSVS)
def test_twirl_sampling_serializer_round_trip(ssv):
    node = TwirlSamplingNode("lhs", "rhs", UniformPauli(10))
    data = TwirlSamplingNodeSerializer.serialize(node, ssv)
    orjson.dumps(data)
    assert node == TypeSerializer.deserialize(data)


@pytest.mark.parametrize("ssv", LeftU2ParametricMultiplicationNodeSerializer.SSVS)
def test_left_u2_multiplication_serializer_round_trip(ssv):
    node = LeftU2ParametricMultiplicationNode("rz", "a", [0, 1, 2])
    data = LeftU2ParametricMultiplicationNodeSerializer.serialize(node, ssv)
    orjson.dumps(data)
    assert node == TypeSerializer.deserialize(data)


@pytest.mark.parametrize("ssv", RightU2ParametricMultiplicationNodeSerializer.SSVS)
def test_right_u2_multiplication_serializer_round_trip(ssv):
    node = RightU2ParametricMultiplicationNode("rz", "a", [0, 1, 2])
    data = RightU2ParametricMultiplicationNodeSerializer.serialize(node, ssv)
    orjson.dumps(data)
    assert node == TypeSerializer.deserialize(data)
