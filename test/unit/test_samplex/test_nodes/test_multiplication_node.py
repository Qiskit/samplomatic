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

import re

import numpy as np
import pytest

from samplomatic.annotations import VirtualType
from samplomatic.distributions import HaarU2, UniformPauli
from samplomatic.exceptions import SamplexConstructionError
from samplomatic.samplex.nodes import LeftMultiplicationNode, RightMultiplicationNode
from samplomatic.virtual_registers import U2Register


class TestLeftMultiplicationNode:
    def test_instantiation_errors(self):
        """Test that errors are properly raised during instantiation"""
        with pytest.raises(
            SamplexConstructionError,
            match=re.escape("Expected fixed operand to have only one sample but it has 7"),
        ):
            LeftMultiplicationNode(U2Register.identity(5, 7), "a")

    @pytest.mark.parametrize("distribution_type", [HaarU2, UniformPauli])
    def test_multiply(self, distribution_type, rng):
        """Test left multiply"""
        operand = distribution_type(5).sample(1, rng)
        register = distribution_type(5).sample(7, rng)
        node = LeftMultiplicationNode(operand, "a")
        assert node.outgoing_register_type is operand.TYPE

        registers = {"a": register.copy()}
        node.evaluate(registers, [])

        assert list(registers) == ["a"]
        assert np.allclose(operand.multiply(register).virtual_gates, registers["a"].virtual_gates)

    def test_writes_to(self):
        """Test writes to"""
        node = LeftMultiplicationNode(U2Register.identity(3, 1), "a")
        assert node.writes_to() == {"a": ({0, 1, 2}, VirtualType.U2)}
        assert node.outgoing_register_type is VirtualType.U2


class TestRightMultiplicationNode:
    def test_instantiation_errors(self):
        """Test that errors are properly raised during instantiation"""
        with pytest.raises(
            SamplexConstructionError,
            match=re.escape("Expected fixed operand to have only one sample but it has 7"),
        ):
            RightMultiplicationNode(U2Register.identity(5, 7), "a")

    @pytest.mark.parametrize("distribution_type", [HaarU2, UniformPauli])
    def test_multiply(self, distribution_type, rng):
        """Test left multiply"""
        operand = distribution_type(5).sample(1, rng)
        register = distribution_type(5).sample(7, rng)
        node = RightMultiplicationNode(operand, "a")
        assert node.outgoing_register_type is operand.TYPE

        registers = {"a": register.copy()}
        node.evaluate(registers, [])

        assert list(registers) == ["a"]
        assert np.allclose(register.multiply(operand).virtual_gates, registers["a"].virtual_gates)

    def test_writes_to(self):
        """Test writes to"""
        node = RightMultiplicationNode(U2Register.identity(3, 1), "a")
        assert node.writes_to() == {"a": ({0, 1, 2}, VirtualType.U2)}
        assert node.outgoing_register_type is VirtualType.U2
