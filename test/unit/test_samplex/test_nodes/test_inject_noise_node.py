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
from samplomatic.samplex import MetadataSpecification, SamplexInput
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
    maps = MetadataSpecification("noise_maps")
    scale = MetadataSpecification("noise_scales", optional=True)
    local_scale = MetadataSpecification("local_scales", optional=True)

    noise_maps = {"my_noise": PauliLindbladMap.from_list([("III", 0)])}
    samplex_input = SamplexInput([], [maps, scale, local_scale], 100)
    samplex_input.validate_and_update(noise_maps=noise_maps)
    node.sample(registers, rng, samplex_input)
    assert registers["injection"] == PauliRegister(np.zeros(300, dtype=np.uint8).reshape(3, 100))
    assert registers["the_sign"] == Z2Register(np.ones((1, 100), dtype=np.uint8))

    noise_maps = {"my_noise": PauliLindbladMap.from_list([("XXX", -100)])}
    samplex_input.validate_and_update(noise_maps=noise_maps)
    node.sample(registers, rng, samplex_input)
    assert (~registers["the_sign"].virtual_gates).any()

    noise_scales = {"my_modifier": 0}
    samplex_input.validate_and_update(noise_maps=noise_maps, noise_scales=noise_scales)
    node.sample(registers, rng, samplex_input)
    assert registers["the_sign"] == Z2Register(np.ones((1, 100), dtype=np.uint8))

    local_scales = {"my_modifier": [0]}
    samplex_input.validate_and_update(
        noise_maps=noise_maps, noise_scales=noise_scales, local_scales=local_scales
    )
    node.sample(registers, rng, samplex_input)
    assert registers["the_sign"] == Z2Register(np.ones((1, 100), dtype=np.uint8))


def test_sample_raises(rng):
    """Test the raises for the sampe method."""
    registers = {}
    node = InjectNoiseNode("injection", "the_sign", "my_noise", 3, "my_modifier")
    maps = MetadataSpecification("noise_maps")
    scale = MetadataSpecification("noise_scales", optional=True)
    local_scale = MetadataSpecification("local_scales", optional=True)
    samplex_input = SamplexInput([], [maps, scale, local_scale], 10)

    noise_maps = {"my_noise": PauliLindbladMap.from_list([("II", 0)])}
    samplex_input.validate_and_update(noise_maps=noise_maps)
    with pytest.raises(SamplexRuntimeError, match="Received a noise map acting on `2`"):
        node.sample(registers, rng, samplex_input)

    noise_maps = {"my_noise": PauliLindbladMap.from_list([("III", 0)])}
    scale = {"my_modifier": [0, 0]}
    samplex_input.validate_and_update(noise_maps=noise_maps, local_scales={"my_modifier": [0, 0]})
    with pytest.raises(SamplexRuntimeError, match="a local scale from reference 'my_modifier'"):
        node.sample(registers, rng, samplex_input)
