# This code is a Qiskit project.
#
# (C) Copyright IBM 2025, 2026.
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
from qiskit.quantum_info import PauliLindbladMap

from samplomatic.samplex.nodes import InjectNoiseNode, InjectNoiseWithHistoryNode
from samplomatic.tensor_interface import (
    PauliLindbladMapSpecification,
    TensorInterface,
    TensorSpecification,
)
from samplomatic.virtual_registers import PauliRegister, VirtualType, Z2Register


def test_instantiates():
    """Test instantiation and basic attributes."""
    node = InjectNoiseNode("injection", "the_sign", "my_noise", 3)
    assert node.instantiates() == {
        "injection": (3, VirtualType.PAULI),
        "the_sign": (1, VirtualType.Z2),
    }
    assert node.outgoing_register_type is VirtualType.PAULI


def test_equality(dummy_sampling_node):
    """Test equality."""
    node = InjectNoiseNode("inject", "sign", "noise", "modifier", 5)
    assert node == node
    assert node == InjectNoiseNode("inject", "sign", "noise", "modifier", 5)
    assert node != dummy_sampling_node()
    assert node != InjectNoiseNode("my_inject", "sign", "noise", "modifier", 5)
    assert node != InjectNoiseNode("inject", "my_sign", "noise", "modifier", 5)
    assert node != InjectNoiseNode("inject", "sign", "my_noise", "modifier", 5)
    assert node != InjectNoiseNode("inject", "sign", "noise", "my_modifier", 5)
    assert node != InjectNoiseNode("inject", "sign", "noise", "modifier", 7)


def test_sample(rng):
    """Test the sample method."""
    registers = {}
    node = InjectNoiseNode("injection", "the_sign", "my_noise", 3, "my_modifier")

    pauli_lindblad_maps = {"my_noise": PauliLindbladMap.from_list([("III", 0.0)])}
    samplex_input = (
        TensorInterface(
            [
                PauliLindbladMapSpecification("pauli_lindblad_maps.my_noise", 3, 1),
                TensorSpecification("noise_scales.my_modifier", (), np.float64),
                TensorSpecification("local_scales.my_modifier", (1,), np.float64),
            ]
        )
        .bind(noise_scales={"my_modifier": 1.0})
        .bind(local_scales={"my_modifier": [1.0]})
        .bind(pauli_lindblad_maps=pauli_lindblad_maps)
    )
    node.sample(registers, rng, samplex_input, 5)
    assert registers["injection"] == PauliRegister(np.zeros(15, dtype=np.uint8).reshape(3, 5))
    assert registers["the_sign"] == Z2Register(np.zeros((1, 5), dtype=np.uint8))

    # via binomial concentration around p=0.5, we can be very confident at least 20 are flipped
    samplex_input["pauli_lindblad_maps.my_noise"] = PauliLindbladMap.from_list([("XXX", -100.0)])
    node.sample(registers, rng, samplex_input, 100)
    assert registers["the_sign"].virtual_gates.sum() > 20

    samplex_input.bind(noise_scales={"my_modifier": 0.0})
    node.sample(registers, rng, samplex_input, 100)
    assert registers["the_sign"] == Z2Register(np.zeros((1, 100), dtype=np.uint8))

    samplex_input.bind(noise_scales={"my_modifier": 1.0}, local_scales={"my_modifier": [0.0]})
    node.sample(registers, rng, samplex_input, 100)
    assert registers["the_sign"] == Z2Register(np.zeros((1, 100), dtype=np.uint8))


def test_history_instantiates():
    """Test that the history register is always instantiated by the history-tracking node."""
    node = InjectNoiseWithHistoryNode("injection", "the_sign", "my_noise", 3, "the_history")
    assert node.instantiates() == {
        "injection": (3, VirtualType.PAULI),
        "the_sign": (1, VirtualType.Z2),
        "the_history": (1, VirtualType.Z2),
    }
    assert node.outgoing_register_type is VirtualType.PAULI


def test_history_equality(dummy_sampling_node):
    """Test equality for the history-tracking node."""
    node = InjectNoiseWithHistoryNode("inject", "sign", "noise", 5, "history", "modifier")
    assert node == node
    assert node == InjectNoiseWithHistoryNode("inject", "sign", "noise", 5, "history", "modifier")
    assert node != dummy_sampling_node()
    assert node != InjectNoiseWithHistoryNode("inject", "sign", "noise", 5, "other", "modifier")
    assert node != InjectNoiseWithHistoryNode("inject", "sign", "noise", 5, "history", "other")
    # A base InjectNoiseNode with otherwise-identical fields is not equal to the history node.
    assert node != InjectNoiseNode("inject", "sign", "noise", 5, "modifier")
    assert InjectNoiseNode("inject", "sign", "noise", 5, "modifier") != node


def test_history_sample(rng):
    """Test that the history register is populated during sampling."""
    registers = {}
    node = InjectNoiseWithHistoryNode("injection", "the_sign", "my_noise", 3, "the_history")

    # First generator has rate 0 (never sampled), the second has a large rate
    # (sampled with probability approaching 0.5).
    pauli_lindblad_maps = {"my_noise": PauliLindbladMap.from_list([("XXX", 0.0), ("ZZZ", 100.0)])}
    samplex_input = TensorInterface(
        [PauliLindbladMapSpecification("pauli_lindblad_maps.my_noise", 3, 2)]
    ).bind(pauli_lindblad_maps=pauli_lindblad_maps)

    node.sample(registers, rng, samplex_input, 100)
    history = registers["the_history"].virtual_gates
    # Two generators, 100 randomizations -> flattened to shape (1, 200).
    assert history.shape == (1, 200)
    # ``pauli_history`` has shape (num_randomizations, num_terms); reshape to recover the axes.
    history = history.reshape(100, 2)
    # The zero-rate generator is never sampled.
    assert history[:, 0].sum() == 0
    # The large-rate generator is sampled at least once (with p~0.5, all-zero is astronomically
    # unlikely across 100 randomizations).
    assert history[:, 1].sum() > 0
