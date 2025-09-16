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
from qiskit.quantum_info import QubitSparsePauliList

from samplomatic.annotations import VirtualType
from samplomatic.samplex.nodes import InjectNoiseNode
from samplomatic.tensor_interface import (
    Specification,
    TensorInterface,
    TensorSpecification,
    ValueType,
)
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
        TensorInterface(
            [
                Specification("noise_maps.paulis.my_noise", ValueType.PAULIS),
                TensorSpecification("noise_maps.rates.my_noise", (1,), np.float64),
                TensorSpecification("noise_scales.my_modifier", (), np.float64),
                TensorSpecification("local_scales.my_modifier", (1,), np.float64),
            ]
        )
        .bind(noise_scales={"my_modifier": 1.0})
        .bind(local_scales={"my_modifier": [1.0]})
        .bind(
            noise_maps={
                "paulis.my_noise": QubitSparsePauliList.from_list(["III"]),
                "rates.my_noise": [0.0],
            }
        )
    )
    node.sample(registers, rng, samplex_input, 5)
    assert registers["injection"] == PauliRegister(np.zeros(15, dtype=np.uint8).reshape(3, 5))
    assert registers["the_sign"] == Z2Register(np.ones((1, 5), dtype=np.uint8))

    samplex_input.bind(
        noise_maps={
            "paulis.my_noise": QubitSparsePauliList.from_list(["XXX"]),
            "rates.my_noise": [-100.0],
        }
    )
    node.sample(registers, rng, samplex_input, num_randomizations=100)
    assert (~registers["the_sign"].virtual_gates).any()

    samplex_input.bind(noise_scales={"my_modifier": 0.0})
    node.sample(registers, rng, samplex_input, 100)
    assert registers["the_sign"] == Z2Register(np.ones((1, 100), dtype=np.uint8))

    samplex_input.bind(noise_scales={"my_modifier": 1.0}, local_scales={"my_modifier": [0.0]})
    node.sample(registers, rng, samplex_input, 100)
    assert registers["the_sign"] == Z2Register(np.ones((1, 100), dtype=np.uint8))
