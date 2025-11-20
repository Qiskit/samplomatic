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

"""Test the UniformC1 distribution"""

from samplomatic.annotations import VirtualType
from samplomatic.distributions import HaarU2, UniformC1


def test_attributes():
    """Test basic attributes of the distribution class."""
    distribution = UniformC1(13)

    assert distribution.num_subsystems == 13
    assert distribution.register_type is VirtualType.C1


def test_equality():
    """Test equality."""
    distribution = UniformC1(13)
    assert distribution == distribution
    assert distribution == UniformC1(13)
    assert distribution != HaarU2(13)
    assert distribution != UniformC1(17)


def test_sample(rng):
    """Test the distribution is behaving sensibly."""
    assert UniformC1(1).sample(1, rng).shape == (1, 1)
    assert UniformC1(8).sample(1, rng).shape == (8, 1)
    assert UniformC1(8).sample(100, rng).shape == (8, 100)

    assert UniformC1(1).sample(1, rng).virtual_gates.shape == (1, 1)
    assert UniformC1(8).sample(1, rng).virtual_gates.shape == (8, 1)
    assert UniformC1(8).sample(100, rng).virtual_gates.shape == (8, 100)
