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

"""Test the PauliRegister distribution"""

import numpy as np
import pytest

from samplomatic.distributions import HaarU2, UniformPauliSubset
from samplomatic.virtual_registers import PauliRegister, VirtualType


def test_attributes():
    """Test basic attributes of the distribution class."""
    distribution = UniformPauliSubset(13, np.array([[1]]))

    assert distribution.num_subsystems == 13
    assert distribution.register_type is VirtualType.PAULI
    assert np.array_equal(distribution.paulis, [[1]])

    distribution = UniformPauliSubset(12, np.array([[1, 2, 3]]))

    assert np.array_equal(distribution.paulis, [[1, 2, 3]])


def test_init_errors():
    """Test that initialization fails if the Paulis are incompatible with number of subsystems."""
    with pytest.raises(ValueError, match="must be divisible by"):
        UniformPauliSubset(13, np.array([[1, 2, 3]]))


def test_equality():
    """Test equality."""
    distribution = UniformPauliSubset(13, np.array([[1]]))
    assert distribution == distribution
    assert distribution == UniformPauliSubset(13, np.array([[1]]))
    assert distribution != UniformPauliSubset(17, np.array([[1]]))
    assert distribution != UniformPauliSubset(13, np.array([[2]]))
    assert distribution != HaarU2(13)


def test_sample(rng):
    """Test the distribution is behaving sensibly."""
    assert UniformPauliSubset(1, np.array([[1]])).sample(1, rng) == PauliRegister([[1]])
    assert UniformPauliSubset(8, np.array([[1]])).sample(1, rng) == PauliRegister([[1]] * 8)
    assert UniformPauliSubset(8, np.array([[1, 2]])).sample(1, rng) == PauliRegister([[1], [2]] * 4)
    assert UniformPauliSubset(6, np.array([[1, 2, 0]])).sample(1, rng) == PauliRegister(
        [[1], [2], [0]] * 2
    )

    samples = UniformPauliSubset(2, np.array([[1, 3], [0, 2]])).sample(100, rng)
    counts = {}
    for sample in samples.virtual_gates:
        if (key_sample := tuple(sample)) not in counts:
            counts[key_sample] = 0
        counts[key_sample] += 1
    assert len(counts) == 2 and all(count > 0 for count in counts.values())
