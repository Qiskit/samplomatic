# This code is a Qiskit project.
#
# (C) Copyright IBM 2025-2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Test the PauliRegister distribution"""

import numpy as np
import pytest

from samplomatic.distributions import BalancedUniformPauli, HaarU2
from samplomatic.virtual_registers import VirtualType


def test_attributes():
    """Test basic attributes of the distribution class."""
    distribution = BalancedUniformPauli(13)

    assert distribution.num_subsystems == 13
    assert distribution.register_type is VirtualType.PAULI


def test_equality():
    """Test equality."""
    distribution = BalancedUniformPauli(13)
    assert distribution == distribution
    assert distribution == BalancedUniformPauli(13)
    assert distribution != HaarU2(13)
    assert distribution != BalancedUniformPauli(17)


def test_sample(rng):
    """Test the distribution is behaving sensibly."""
    assert BalancedUniformPauli(1).sample(1, rng).shape == (1, 1)
    assert BalancedUniformPauli(8).sample(1, rng).shape == (8, 1)
    assert BalancedUniformPauli(8).sample(100, rng).shape == (8, 100)
    assert BalancedUniformPauli(8).sample(101, rng).shape == (8, 101)
    assert BalancedUniformPauli(8).sample(102, rng).shape == (8, 102)
    assert BalancedUniformPauli(8).sample(103, rng).shape == (8, 103)
    assert BalancedUniformPauli(8).sample(104, rng).shape == (8, 104)


@pytest.mark.parametrize("num_samples", [0, 3, 4, 7, 11, 10, 16])
def test_balanced_by_four(rng, num_samples):
    """Test that Paulis are balanced on each qubit."""
    paulis = BalancedUniformPauli(5).sample(num_samples, rng)

    min_expected = num_samples // 4
    max_expected = min_expected + bool(num_samples % 4)

    for pauli in [0, 2, 3, 1]:
        pauli_count = np.sum(paulis.virtual_gates == pauli, axis=1)
        assert np.all((pauli_count == min_expected) | (pauli_count == max_expected))
        assert np.all((pauli_count == min_expected) | (pauli_count == max_expected))
        assert np.all((pauli_count == min_expected) | (pauli_count == max_expected))
        assert np.all((pauli_count == min_expected) | (pauli_count == max_expected))


@pytest.mark.parametrize("num_samples", [0, 6, 8])
def test_balanced_by_two(rng, num_samples):
    """Test that Paulis are balanced on each qubit with respect to pi pulses."""
    paulis = BalancedUniformPauli(5).sample(num_samples, rng)

    # I,X,Y,Z = 0,2,3,1, therefore 'pauli // 2 == 1' means we have an X or Y
    is_pi_pulse = paulis.virtual_gates // 2 == 1

    assert np.all(np.sum(is_pi_pulse, axis=1) == num_samples // 2)


def test_consecutive(rng):
    """Test that the balancings are consecutive"""
    paulis = BalancedUniformPauli(3).sample(4 * 5, rng)

    for idx_qubit in range(paulis.num_subsystems):
        for idx_group in range(0, 20, 4):
            subset = set(map(int, paulis.virtual_gates[idx_qubit, idx_group : idx_group + 4]))
            assert subset == {0, 1, 2, 3}
