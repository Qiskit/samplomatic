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

"""Test the PauliRegister"""

from samplomatic.annotations import VirtualType
from samplomatic.virtual_registers import (
    C1Register,
    VirtualRegister,
)


def test_select():
    """Test that we can select from a VirtualType."""
    assert VirtualRegister.select(VirtualType.C1) is C1Register


def test_convert_to_c1():
    """Test the convert_to() method returns the register when types match."""
    cliffords = C1Register.identity(3, 3)
    assert cliffords is cliffords.convert_to(VirtualType.C1)


def test_multiply():
    """Test the multiply() method."""
    lhs = C1Register([[[[0, 1, 0], [1, 1, 0]]]])
    rhs = C1Register([[[[1, 1, 0], [1, 0, 0]]]])

    assert lhs.multiply(rhs) == C1Register.identity(1, 1)
    assert lhs == C1Register([[[[0, 1, 0], [1, 1, 0]]]])
    assert rhs == C1Register([[[[1, 1, 0], [1, 0, 0]]]])

    lhs = C1Register([[[[1, 1, 0], [0, 1, 0]]]])
    rhs = C1Register([[[[0, 1, 0], [1, 0, 0]]]])

    assert lhs.multiply(rhs) == C1Register([[[[0, 1, 0], [1, 1, 0]]]])


def test_multiply_with_subinds():
    """Test the multiply() method with sub indices"""
    lhs = C1Register([[[[1, 0, 0], [0, 1, 1]]], [[[0, 1, 0], [1, 1, 0]]]])
    rhs = C1Register([[[[1, 1, 0], [1, 0, 0]]]])

    assert lhs.multiply(rhs, subsystem_idxs=[1]) == C1Register.identity(1, 1)
    assert lhs == C1Register([[[[1, 0, 0], [0, 1, 1]]], [[[0, 1, 0], [1, 1, 0]]]])
    assert rhs == C1Register([[[[1, 1, 0], [1, 0, 0]]]])


def test_inplace_multiply():
    """Test the inplace_multiply() method."""
    lhs = C1Register([[[[0, 1, 0], [1, 1, 0]]]])
    rhs = C1Register([[[[1, 1, 0], [1, 0, 0]]]])

    lhs.inplace_multiply(rhs)
    assert lhs == C1Register.identity(1, 1)
    assert rhs == C1Register([[[[1, 1, 0], [1, 0, 0]]]])

    lhs = C1Register([[[[1, 1, 0], [0, 1, 0]]]])
    rhs = C1Register([[[[0, 1, 0], [1, 0, 0]]]])
    lhs.inplace_multiply(rhs)

    assert lhs == C1Register([[[[0, 1, 0], [1, 1, 0]]]])


def test_inplace_multiply_with_subinds():
    """Test the inplace_multiply() method with sub indices"""
    lhs = C1Register([[[[1, 0, 0], [0, 1, 1]]], [[[0, 1, 0], [1, 1, 0]]]])
    rhs = C1Register([[[[1, 1, 0], [1, 0, 0]]]])

    lhs.inplace_multiply(rhs, [1])
    assert lhs == C1Register([[[[1, 0, 0], [0, 1, 1]]], [[[1, 0, 0], [0, 1, 0]]]])
    assert rhs == C1Register([[[[1, 1, 0], [1, 0, 0]]]])


def test_left_multiply():
    """Test the left_multiply() method."""
    lhs = C1Register([[[[0, 1, 0], [1, 1, 0]]]])
    rhs = C1Register([[[[1, 1, 0], [1, 0, 0]]]])

    assert lhs.left_multiply(rhs) == C1Register.identity(1, 1)
    assert lhs == C1Register([[[[0, 1, 0], [1, 1, 0]]]])
    assert rhs == C1Register([[[[1, 1, 0], [1, 0, 0]]]])

    lhs = C1Register([[[[1, 1, 0], [0, 1, 0]]]])
    rhs = C1Register([[[[0, 1, 0], [1, 0, 0]]]])

    assert lhs.left_multiply(rhs) == C1Register([[[[1, 1, 1], [1, 0, 0]]]])


def test_left_multiply_with_subinds():
    """Test the left_multiply() method with sub indices."""
    lhs = C1Register([[[[1, 0, 0], [0, 1, 1]]], [[[0, 1, 0], [1, 1, 0]]]])
    rhs = C1Register([[[[1, 1, 0], [1, 0, 0]]]])

    assert lhs.left_multiply(rhs, subsystem_idxs=[1]) == C1Register.identity(1, 1)
    assert lhs == C1Register([[[[1, 0, 0], [0, 1, 1]]], [[[0, 1, 0], [1, 1, 0]]]])
    assert rhs == C1Register([[[[1, 1, 0], [1, 0, 0]]]])


def test_left_inplace_multiply():
    """Test the left_inplace_multiply() method."""
    lhs = C1Register([[[[0, 1, 0], [1, 1, 0]]]])
    rhs = C1Register([[[[1, 1, 0], [1, 0, 0]]]])

    lhs.left_inplace_multiply(rhs)
    assert lhs == C1Register.identity(1, 1)
    assert rhs == C1Register([[[[1, 1, 0], [1, 0, 0]]]])

    lhs = C1Register([[[[1, 1, 0], [0, 1, 0]]]])
    rhs = C1Register([[[[0, 1, 0], [1, 0, 0]]]])

    lhs.left_inplace_multiply(rhs)
    assert lhs == C1Register([[[[1, 1, 1], [1, 0, 0]]]])


def test_left_inplace_multiply_with_subinds():
    """Test the left_inplace_multiply() method with sub indices"""
    lhs = C1Register([[[[1, 0, 0], [0, 1, 1]]], [[[0, 1, 0], [1, 1, 0]]]])
    rhs = C1Register([[[[1, 1, 0], [1, 0, 0]]]])

    lhs.left_inplace_multiply(rhs, subsystem_idxs=[1])
    assert lhs == C1Register([[[[1, 0, 0], [0, 1, 1]]], [[[1, 0, 0], [0, 1, 0]]]])
    assert rhs == C1Register([[[[1, 1, 0], [1, 0, 0]]]])


def test_invert():
    """Test the invert() method."""
    cliffords = C1Register([[[[0, 1, 0], [1, 0, 0]], [[1, 1, 0], [1, 0, 0]]]])
    inverted = cliffords.invert()

    assert inverted == C1Register([[[[0, 1, 0], [1, 0, 0]], [[0, 1, 0], [1, 1, 0]]]])
