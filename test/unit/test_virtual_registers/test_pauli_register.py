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

import numpy as np

from samplomatic.annotations import VirtualType
from samplomatic.virtual_registers import PauliRegister, U2Register, VirtualRegister, Z2Register


def test_select():
    """Test that we can select from a VirtualType."""
    assert VirtualRegister.select(VirtualType.PAULI) is PauliRegister


def test_mod_on_construct():
    """Test that the constructor mods to integers to 0-3."""
    paulis = PauliRegister([[5, 6, 7, 8]])
    assert np.array_equal(paulis.virtual_gates, [[1, 2, 3, 0]])


def test_mod_on_set():
    """Test that the setter mods to integers to 0-3."""
    paulis = PauliRegister([[0], [1], [2], [3]])
    paulis[[1, 2]] = [[6], [8]]
    assert np.array_equal(paulis.virtual_gates, [[0], [2], [0], [3]])


def test_convert_to_u2():
    """Test the convert_to() method for U2Register."""
    paulis = PauliRegister([[0, 1, 2], [3, 2, 1]])
    u2 = paulis.convert_to(VirtualType.U2)

    assert isinstance(u2, U2Register)
    assert u2.num_subsystems == 2
    assert u2.num_samples == 3

    assert np.allclose(u2.virtual_gates[0, 0], np.diag([1, 1]))
    assert np.allclose(u2.virtual_gates[0, 1], np.diag([1, -1]))
    assert np.allclose(u2.virtual_gates[0, 2], np.diag([1, 1])[::-1])

    assert np.allclose(u2.virtual_gates[1, 0], np.diag([-1j, 1j])[::-1])
    assert np.allclose(u2.virtual_gates[1, 1], np.diag([1, 1])[::-1])
    assert np.allclose(u2.virtual_gates[1, 2], np.diag([1, -1]))


def test_convert_to_z2():
    """Test the convert_to() method for Z2Register."""
    paulis = PauliRegister([[0, 1, 2], [3, 2, 1]])
    z2 = paulis.convert_to(VirtualType.Z2)

    assert isinstance(z2, Z2Register)
    assert z2.num_subsystems == 2
    assert z2.num_samples == 3

    assert np.allclose(z2.virtual_gates, [[False, False, True], [True, True, False]])


def test_convert_to_pauli():
    """Test the convert_to() method returns the register when types match."""
    paulis = PauliRegister([[0, 1, 2], [3, 2, 1]])
    assert paulis is paulis.convert_to(VirtualType.PAULI)


def test_multiply():
    """Test the multiply() method."""
    lhs = PauliRegister([[0, 1, 2], [2, 2, 1]])
    rhs = PauliRegister([[0, 0, 0], [1, 1, 1]])

    assert lhs.multiply(rhs) == PauliRegister([[0, 1, 2], [3, 3, 0]])
    assert lhs == PauliRegister([[0, 1, 2], [2, 2, 1]])
    assert rhs == PauliRegister([[0, 0, 0], [1, 1, 1]])


def test_multiply_with_subinds():
    """Test the multiply() method with sub indices"""
    lhs = PauliRegister([[0, 1, 2], [2, 2, 1]])
    rhs = PauliRegister([[1, 1, 1]])

    assert lhs.multiply(rhs, subsystem_idxs=[1]) == PauliRegister([[3, 3, 0]])
    assert lhs == PauliRegister([[0, 1, 2], [2, 2, 1]])
    assert rhs == PauliRegister([[1, 1, 1]])


def test_inplace_multiply():
    """Test the inplace_multiply() method."""
    lhs = PauliRegister([[0, 1, 2], [2, 2, 1]])
    rhs = PauliRegister([[0, 0, 0], [1, 1, 1]])

    lhs.inplace_multiply(rhs)
    assert lhs == PauliRegister([[0, 1, 2], [3, 3, 0]])
    assert rhs == PauliRegister([[0, 0, 0], [1, 1, 1]])


def test_inplace_multiply_with_subinds():
    """Test the inplace_multiply() method with sub indices"""
    lhs = PauliRegister([[0, 1, 2], [2, 2, 1]])
    rhs = PauliRegister([[1, 1, 1]])

    lhs.inplace_multiply(rhs, subsystem_idxs=[1])
    assert lhs == PauliRegister([[0, 1, 2], [3, 3, 0]])
    assert rhs == PauliRegister([[1, 1, 1]])


def test_left_multiply():
    """Test the left_multiply() method."""
    rhs = PauliRegister([[0, 1, 2], [2, 2, 1]])
    lhs = PauliRegister([[0, 0, 0], [1, 1, 1]])

    assert rhs.multiply(lhs) == PauliRegister([[0, 1, 2], [3, 3, 0]])
    assert rhs == PauliRegister([[0, 1, 2], [2, 2, 1]])
    assert lhs == PauliRegister([[0, 0, 0], [1, 1, 1]])


def test_left_multiply_with_subinds():
    """Test the left_multiply() method with sub indices."""
    rhs = PauliRegister([[0, 1, 2], [2, 2, 1]])
    lhs = PauliRegister([[1, 1, 1]])

    assert rhs.multiply(lhs, subsystem_idxs=[1]) == PauliRegister([[3, 3, 0]])
    assert rhs == PauliRegister([[0, 1, 2], [2, 2, 1]])
    assert lhs == PauliRegister([[1, 1, 1]])


def test_left_inplace_multiply():
    """Test the left_inplace_multiply() method."""
    rhs = PauliRegister([[0, 1, 2], [2, 2, 1]])
    lhs = PauliRegister([[0, 0, 0], [1, 1, 1]])

    rhs.inplace_multiply(lhs)
    assert rhs == PauliRegister([[0, 1, 2], [3, 3, 0]])
    assert lhs == PauliRegister([[0, 0, 0], [1, 1, 1]])


def test_left_inplace_multiply_with_subinds():
    """Test the left_inplace_multiply() method with sub indices"""
    rhs = PauliRegister([[0, 1, 2], [2, 2, 1]])
    lhs = PauliRegister([[1, 1, 1]])

    rhs.inplace_multiply(lhs, subsystem_idxs=[1])
    assert rhs == PauliRegister([[0, 1, 2], [3, 3, 0]])
    assert lhs == PauliRegister([[1, 1, 1]])


def test_invert():
    """Test the invert() method."""
    paulis = PauliRegister([[0, 1, 2], [2, 2, 1]])
    inverted = paulis.invert()

    assert paulis == inverted
    paulis[0, 0] = 2
    assert inverted.virtual_gates[0, 0] != 2
