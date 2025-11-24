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

"""Test the FiniteGroupRegister"""

import numpy as np
import pytest

from samplomatic.serializable import TYPE_REGISTRY
from samplomatic.virtual_registers.finite_group_register import FiniteGroupRegister


@pytest.fixture
def s3_register():
    original_registry = TYPE_REGISTRY.copy()

    class S3Register(FiniteGroupRegister):
        """Virtual register of the symmetric group over 3 elements."""

        GATE_SHAPE = ()
        SUBSYSTEM_SIZE = 1
        DTYPE = np.uint8

        @property
        def lookup_table(self):
            return np.array(
                [
                    [0, 1, 2, 3, 4, 5],
                    [1, 0, 4, 5, 2, 3],
                    [2, 5, 0, 4, 3, 1],
                    [3, 4, 5, 0, 1, 2],
                    [4, 3, 1, 2, 5, 0],
                    [5, 2, 3, 1, 0, 4],
                ],
                dtype=np.uint8,
            )

        @property
        def inverse_table(self):
            return np.array([0, 1, 2, 3, 5, 4], dtype=np.uint8)

        @classmethod
        def identity(cls, num_subsystems, num_samples):
            arr = np.zeros((num_subsystems, num_samples), dtype=np.uint8)
            return cls(arr)

    yield S3Register
    TYPE_REGISTRY.clear()
    TYPE_REGISTRY.update(original_registry)


def test_attributes(s3_register):
    """Test the basic attributes."""
    assert s3_register.identity(1, 1).num_elements == 6


def test_invert(s3_register):
    """Test the invert() method."""
    register = s3_register(np.array([[0, 1, 2], [3, 4, 5]])).invert()
    assert register == s3_register(np.array([[0, 1, 2], [3, 5, 4]]))


def test_multiply(s3_register):
    """Test the multiply() method."""
    lhs = s3_register([[0, 1, 2], [3, 4, 5]])
    rhs = s3_register([[4, 4, 4], [4, 4, 4]])

    assert lhs.multiply(rhs) == s3_register([[4, 2, 3], [1, 5, 0]])
    assert lhs == s3_register([[0, 1, 2], [3, 4, 5]])
    assert rhs == s3_register([[4, 4, 4], [4, 4, 4]])

    assert lhs.multiply(lhs.invert()) == s3_register.identity(2, 3)


def test_multiply_subinds(s3_register):
    """Test the multiply() method with indices."""
    lhs = s3_register([[0, 1, 2], [3, 4, 5]])
    rhs = s3_register([[4, 4, 4]])

    assert lhs.multiply(rhs, [1]) == s3_register([[1, 5, 0]])
    assert lhs == s3_register([[0, 1, 2], [3, 4, 5]])
    assert rhs == s3_register([[4, 4, 4]])


def test_inplace_multiply(s3_register):
    """Test the inplace_multiply() method."""
    lhs = s3_register([[0, 1, 2], [3, 4, 5]])
    rhs = s3_register([[4, 4, 4], [4, 4, 4]])

    lhs.inplace_multiply(rhs)
    assert lhs == s3_register([[4, 2, 3], [1, 5, 0]])
    assert rhs == s3_register([[4, 4, 4], [4, 4, 4]])


def test_inplace_multiply_subinds(s3_register):
    """Test the inplace_multiply() method with indices."""
    lhs = s3_register([[0, 1, 2], [3, 4, 5]])
    rhs = s3_register([[4, 4, 4]])

    lhs.inplace_multiply(rhs, [1])
    assert lhs == s3_register([[0, 1, 2], [1, 5, 0]])
    assert rhs == s3_register([[4, 4, 4]])


def test_left_multiply(s3_register):
    """Test the left_multiply() method."""
    lhs = s3_register([[0, 1, 2], [3, 4, 5]])
    rhs = s3_register([[4, 4, 4], [4, 4, 4]])

    assert lhs.left_multiply(rhs) == s3_register([[4, 3, 1], [2, 5, 0]])
    assert lhs == s3_register([[0, 1, 2], [3, 4, 5]])
    assert rhs == s3_register([[4, 4, 4], [4, 4, 4]])


def test_left_multiply_subinds(s3_register):
    """Test the left_multiply() method with indices."""
    lhs = s3_register([[0, 1, 2], [3, 4, 5]])
    rhs = s3_register([[4, 4, 4]])

    assert lhs.left_multiply(rhs, [0]) == s3_register([[4, 3, 1]])
    assert lhs == s3_register([[0, 1, 2], [3, 4, 5]])
    assert rhs == s3_register([[4, 4, 4]])


def test_left_inplace_multiply(s3_register):
    """Test the left_inplace_multiply() method."""
    lhs = s3_register([[0, 1, 2], [3, 4, 5]])
    rhs = s3_register([[4, 4, 4], [4, 4, 4]])

    lhs.left_inplace_multiply(rhs)
    assert lhs == s3_register([[4, 3, 1], [2, 5, 0]])
    assert rhs == s3_register([[4, 4, 4], [4, 4, 4]])


def test_left_inplace_multiply_subinds(s3_register):
    """Test the left_inplace_multiply() method with indices."""
    lhs = s3_register([[0, 1, 2], [3, 4, 5]])
    rhs = s3_register([[4, 4, 4]])

    lhs.left_inplace_multiply(rhs, [0])
    assert lhs == s3_register([[4, 3, 1], [3, 4, 5]])
    assert rhs == s3_register([[4, 4, 4]])
