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

"""Test the Z2Register"""

import numpy as np

from samplomatic.annotations import VirtualType
from samplomatic.virtual_registers import VirtualRegister, Z2Register


def test_select():
    """Test that we can select from a VirtualType."""
    assert VirtualRegister.select(VirtualType.Z2) is Z2Register


def test_mod_on_construct():
    """Test that the constructor mods to integers to 0-1."""
    reg = Z2Register([[0, 1, 2, 3, 4, 5]])
    assert np.array_equal(reg.virtual_gates, [[0, 1, 0, 1, 0, 1]])


def test_mod_on_set():
    """Test that the setter mods to integers to 0-1."""
    reg = Z2Register([[0], [1], [0], [1]])
    reg[[1, 2]] = [[6], [7]]
    assert np.array_equal(reg.virtual_gates, [[0], [0], [1], [1]])


def test_multiply():
    """Test the multiply() method."""
    lhs = Z2Register([[0, 1, 1], [0, 0, 1]])
    rhs = Z2Register([[0, 0, 0], [1, 1, 1]])

    assert lhs.multiply(rhs) == Z2Register([[0, 1, 1], [1, 1, 0]])
    assert lhs == Z2Register([[0, 1, 1], [0, 0, 1]])
    assert rhs == Z2Register([[0, 0, 0], [1, 1, 1]])


def test_multiply_with_subinds():
    """Test the multiply() method with sub indices."""
    lhs = Z2Register([[0, 1, 1], [0, 0, 1]])
    rhs = Z2Register([[1, 1, 1]])

    assert lhs.multiply(rhs, subsystem_idxs=[1]) == Z2Register([[1, 1, 0]])
    assert lhs == Z2Register([[0, 1, 1], [0, 0, 1]])
    assert rhs == Z2Register([[1, 1, 1]])


def test_inplace_multiply():
    """Test the inplace_multiply() method."""
    lhs = Z2Register([[0, 1, 0], [0, 0, 1]])
    rhs = Z2Register([[0, 0, 0], [1, 1, 1]])

    lhs.inplace_multiply(rhs)
    assert lhs == Z2Register([[0, 1, 0], [1, 1, 0]])
    assert rhs == Z2Register([[0, 0, 0], [1, 1, 1]])


def test_inplace_multiply_with_subinds():
    """Test the inplace_multiply() method with sub indices."""
    lhs = Z2Register([[0, 1, 0], [0, 0, 1]])
    rhs = Z2Register([[1, 1, 1]])

    lhs.inplace_multiply(rhs, subsystem_idxs=[1])
    assert lhs == Z2Register([[0, 1, 0], [1, 1, 0]])
    assert rhs == Z2Register([[1, 1, 1]])


def test_left_multiply():
    """Test the left_multiply() method."""
    rhs = Z2Register([[0, 1, 1], [0, 0, 1]])
    lhs = Z2Register([[0, 0, 0], [1, 1, 1]])

    assert rhs.left_multiply(lhs) == Z2Register([[0, 1, 1], [1, 1, 0]])
    assert rhs == Z2Register([[0, 1, 1], [0, 0, 1]])
    assert lhs == Z2Register([[0, 0, 0], [1, 1, 1]])


def test_left_multiply_with_subinds():
    """Test the left_multiply() method with sub indices."""
    rhs = Z2Register([[0, 1, 1], [0, 0, 1]])
    lhs = Z2Register([[1, 1, 1]])

    assert rhs.left_multiply(lhs, subsystem_idxs=[1]) == Z2Register([[1, 1, 0]])
    assert rhs == Z2Register([[0, 1, 1], [0, 0, 1]])
    assert lhs == Z2Register([[1, 1, 1]])


def test_left_inplace_multiply():
    """Test the left_inplace_multiply() method."""
    rhs = Z2Register([[0, 1, 0], [0, 0, 1]])
    lhs = Z2Register([[0, 0, 0], [1, 1, 1]])

    rhs.left_inplace_multiply(lhs)
    assert rhs == Z2Register([[0, 1, 0], [1, 1, 0]])
    assert lhs == Z2Register([[0, 0, 0], [1, 1, 1]])


def test_left_inplace_multiply_with_subinds():
    """Test the left_inplace_multiply() method with sub indices."""
    rhs = Z2Register([[0, 1, 0], [0, 0, 1]])
    lhs = Z2Register([[1, 1, 1]])

    rhs.left_inplace_multiply(lhs, subsystem_idxs=[1])
    assert rhs == Z2Register([[0, 1, 0], [1, 1, 0]])
    assert lhs == Z2Register([[1, 1, 1]])


def test_invert():
    """Test the invert() method."""
    reg = Z2Register([[1, 1, 0], [0, 0, 1]])
    inverted = reg.invert()
    assert reg == inverted

    reg[0, 0] = 0
    assert inverted.virtual_gates[0, 0] != 0
