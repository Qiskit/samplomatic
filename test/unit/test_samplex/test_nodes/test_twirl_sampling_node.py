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

"""Test the TwirlSamplingNode class"""

from samplomatic.annotations import VirtualType
from samplomatic.distributions import UniformPauli
from samplomatic.samplex.nodes import TwirlSamplingNode
from samplomatic.tensor_interface import TensorInterface
from samplomatic.virtual_registers import PauliRegister


def test_instantiates():
    """Test instantiation and basic attributes."""
    node = TwirlSamplingNode("lhs", "rhs", UniformPauli(10))
    expected_dict = {"lhs": (10, VirtualType.PAULI), "rhs": (10, VirtualType.PAULI)}
    assert node.instantiates() == expected_dict
    assert node.outgoing_register_type is VirtualType.PAULI


def test_sample(rng):
    """Test the sample method."""
    registers = {}
    node = TwirlSamplingNode("lhs", "rhs", UniformPauli(10))
    samplex_input = TensorInterface([])

    node.sample(registers, rng, samplex_input, 5)
    assert registers["lhs"].multiply(registers["rhs"]) == PauliRegister.identity(10, 5)
    assert registers["lhs"].multiply(registers["rhs"]) == PauliRegister.identity(10, 5)
