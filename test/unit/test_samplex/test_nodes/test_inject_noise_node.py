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

"""Test the InjectNoiseNode class"""

import numpy as np
import pytest
from qiskit.quantum_info import PauliLindbladMap

from samplomatic.annotations import VirtualType
from samplomatic.exceptions import SamplexRuntimeError
from samplomatic.samplex.interfaces import (
    SamplexInput,
    Specification,
    TensorSpecification,
    ValueType,
)
from samplomatic.samplex.nodes import InjectNoiseNode
from samplomatic.virtual_registers import PauliRegister, Z2Register


def test_instantiates():
    """Test instantiation and basic attributes."""
    node = InjectNoiseNode("injection", "the_sign", "my_noise", 3)
    assert node.instantiates() == {
        "injection": (3, VirtualType.PAULI),
        "the_sign": (1, VirtualType.Z2),
    }
    assert node.outgoing_register_type is VirtualType.PAULI


def test_sample(rng):
    """Test the sample method."""
    registers = {}
    node = InjectNoiseNode("injection", "the_sign", "my_noise", 3, "my_modifier")

    samplex_input = (
        SamplexInput(
            [
                Specification("my_noise", ValueType.LINDBLAD),
                Specification("num_randomizations", ValueType.INT),
                TensorSpecification("noise_scales.my_modifier", (), np.float64),
                TensorSpecification("local_scales.my_modifier", (1,), np.float64),
            ],
            {"noise_scales.my_modifier": np.float64(1.0), "local_scales.my_modifier": [1.0]},
        )
        .bind(my_noise=PauliLindbladMap.from_list([("III", 0)]))
        .bind(num_randomizations=5)
    )
    node.sample(registers, rng, samplex_input)
    assert registers["injection"] == PauliRegister(np.zeros(15, dtype=np.uint8).reshape(3, 5))
    assert registers["the_sign"] == Z2Register(np.ones((1, 5), dtype=np.uint8))

    samplex_input.bind(my_noise=PauliLindbladMap.from_list([("XXX", -100)])).bind(
        num_randomizations=100
    )
    node.sample(registers, rng, samplex_input)
    assert (~registers["the_sign"].virtual_gates).any()

    samplex_input.bind(noise_scales={"my_modifier": 0.0})
    node.sample(registers, rng, samplex_input)
    assert registers["the_sign"] == Z2Register(np.ones((1, 100), dtype=np.uint8))

    samplex_input.bind(noise_scales={"my_modifier": 1.0}, local_scales={"my_modifier": [0.0]})
    node.sample(registers, rng, samplex_input)
    assert registers["the_sign"] == Z2Register(np.ones((1, 100), dtype=np.uint8))


def test_sample_raises(rng):
    """Test the raises for the sample method."""
    registers = {}
    node = InjectNoiseNode("injection", "the_sign", "my_noise", 3, "my_modifier")

    samplex_input = SamplexInput(
        [
            Specification("num_randomizations", ValueType.INT),
            Specification("my_noise", ValueType.LINDBLAD),
            Specification("local_scales.my_modifier", ValueType.NUMPY_ARRAY),
        ],
        {"local_scales.my_modifier": [1.0]},
    )

    samplex_input.bind(my_noise=PauliLindbladMap.from_list([("II", 0)])).bind(num_randomizations=5)
    with pytest.raises(SamplexRuntimeError, match="Received a noise map acting on `2`"):
        node.sample(registers, rng, samplex_input)

    samplex_input.bind(my_noise=PauliLindbladMap.from_list([("III", 0)]))
    samplex_input.bind(local_scales={"my_modifier": [1.0, 2.0]})
    with pytest.raises(SamplexRuntimeError, match="a local scale from reference 'my_modifier'"):
        node.sample(registers, rng, samplex_input)
