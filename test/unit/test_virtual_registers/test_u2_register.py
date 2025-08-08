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

"""Test the U2Register"""

import numpy as np
from qiskit.quantum_info import random_unitary

from samplomatic.annotations import VirtualType
from samplomatic.virtual_registers import U2Register, VirtualRegister


def test_select():
    """Test that we can select from a VirtualType."""
    assert VirtualRegister.select(VirtualType.U2) is U2Register


def test_multiply():
    """Test the multiply() method."""
    u0, u1, u2 = map(np.array, (random_unitary(2) for _ in range(3)))
    lhs = U2Register([[u0, u1, u2], [u2, u2, u1]])
    rhs = U2Register([[u0, u0, u0], [u1, u1, u1]])

    assert lhs.multiply(rhs) == U2Register(
        [[u0 @ u0, u1 @ u0, u2 @ u0], [u2 @ u1, u2 @ u1, u1 @ u1]]
    )
    assert lhs == U2Register([[u0, u1, u2], [u2, u2, u1]])
    assert rhs == U2Register([[u0, u0, u0], [u1, u1, u1]])


def test_multiply_with_subinds():
    """Test the multiply() method with sub indices"""
    u0, u1, u2 = map(np.array, (random_unitary(2) for _ in range(3)))
    lhs = U2Register([[u0, u1, u2], [u2, u2, u1]])
    rhs = U2Register([[u1, u1, u1]])

    assert lhs.multiply(rhs, subsystem_idxs=[1]) == U2Register([[u2 @ u1, u2 @ u1, u1 @ u1]])
    assert lhs == U2Register([[u0, u1, u2], [u2, u2, u1]])
    assert rhs == U2Register([[u1, u1, u1]])


def test_inplace_multiply():
    """Test the inplace_multiply() method."""
    u0, u1, u2 = map(np.array, (random_unitary(2) for _ in range(3)))
    lhs = U2Register([[u0, u1, u2], [u2, u2, u1]])
    rhs = U2Register([[u0, u0, u0], [u1, u1, u1]])

    lhs.inplace_multiply(rhs)
    assert lhs == U2Register([[u0 @ u0, u1 @ u0, u2 @ u0], [u2 @ u1, u2 @ u1, u1 @ u1]])
    assert rhs == U2Register([[u0, u0, u0], [u1, u1, u1]])


def test_inplace_multiply_with_subinds():
    """Test the inplace_multiply() method with sub indices"""
    u0, u1, u2 = map(np.array, (random_unitary(2) for _ in range(3)))
    lhs = U2Register([[u0, u1, u2], [u2, u2, u1]])
    rhs = U2Register([[u1, u1, u1]])

    lhs.inplace_multiply(rhs, subsystem_idxs=[1])
    assert lhs == U2Register([[u0, u1, u2], [u2 @ u1, u2 @ u1, u1 @ u1]])
    assert rhs == U2Register([[u1, u1, u1]])


def test_left_multiply():
    """Test the multiply() method."""
    u0, u1, u2 = map(np.array, (random_unitary(2) for _ in range(3)))
    rhs = U2Register([[u0, u1, u2], [u2, u2, u1]])
    lhs = U2Register([[u0, u0, u0], [u1, u1, u1]])

    assert rhs.left_multiply(lhs) == U2Register(
        [[u0 @ u0, u0 @ u1, u0 @ u2], [u1 @ u2, u1 @ u2, u1 @ u1]]
    )
    assert rhs == U2Register([[u0, u1, u2], [u2, u2, u1]])
    assert lhs == U2Register([[u0, u0, u0], [u1, u1, u1]])


def test_left_multiply_with_subinds():
    """Test the multiply() method with subindices"""
    u0, u1, u2 = map(np.array, (random_unitary(2) for _ in range(3)))
    rhs = U2Register([[u0, u1, u2], [u2, u2, u1]])
    lhs = U2Register([[u1, u1, u1]])

    assert rhs.left_multiply(lhs, subsystem_idxs=[1]) == U2Register([[u1 @ u2, u1 @ u2, u1 @ u1]])
    assert rhs == U2Register([[u0, u1, u2], [u2, u2, u1]])
    assert lhs == U2Register([[u1, u1, u1]])


def test_left_inplace_multiply():
    """Test the inplace_multiply() method."""
    u0, u1, u2 = map(np.array, (random_unitary(2) for _ in range(3)))
    rhs = U2Register([[u0, u1, u2], [u2, u2, u1]])
    lhs = U2Register([[u0, u0, u0], [u1, u1, u1]])

    rhs.left_inplace_multiply(lhs)
    assert rhs == U2Register([[u0 @ u0, u0 @ u1, u0 @ u2], [u1 @ u2, u1 @ u2, u1 @ u1]])
    assert lhs == U2Register([[u0, u0, u0], [u1, u1, u1]])


def test_left_inplace_multiply_with_subinds():
    """Test the inplace_multiply() method with sub indices"""
    u0, u1, u2 = map(np.array, (random_unitary(2) for _ in range(3)))
    rhs = U2Register([[u0, u1, u2], [u2, u2, u1]])
    lhs = U2Register([[u1, u1, u1]])

    rhs.left_inplace_multiply(lhs, subsystem_idxs=[1])
    assert rhs == U2Register([[u0, u1, u2], [u1 @ u2, u1 @ u2, u1 @ u1]])
    assert lhs == U2Register([[u1, u1, u1]])


def test_invert():
    """Test the invert() method."""
    u0, u1, u2 = map(np.array, (random_unitary(2) for _ in range(3)))
    unitaries = U2Register([[u0, u1, u2], [u2, u2, u1]])
    inverted = unitaries.invert()

    assert inverted == U2Register(
        [[u0.conj().T, u1.conj().T, u2.conj().T], [u2.conj().T, u2.conj().T, u1.conj().T]]
    )


def test_equality():
    """Test the equality dunder works and ignores global phases."""
    u0, u1, u2 = map(np.array, (random_unitary(2) for _ in range(3)))
    a, b, c = np.exp([0.1j, 0.2j, 6j])
    unitaries0 = U2Register([[u0, u1, u2], [u2, u2, u1]])
    unitaries1 = U2Register([[u0, u0, u0], [u1, u1, u1]])
    unitaries3 = U2Register([[u0, u1, u2], [u2, u2, u1]])
    unitaries4 = U2Register([[a * u0, b * u1, c * u2], [u2, a * u2, u1]])

    assert unitaries0 == unitaries0
    assert unitaries0 == unitaries3
    assert unitaries0 == unitaries4
    assert unitaries0 != unitaries1
