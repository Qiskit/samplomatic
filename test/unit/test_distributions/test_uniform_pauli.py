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

"""Test the PauliRegister distribution"""

from samplomatic.annotations import VirtualType
from samplomatic.distributions import UniformPauli


def test_attributes():
    """Test basic attributes of the distribution class."""
    distribution = UniformPauli(13)

    assert distribution.num_subsystems == 13
    assert distribution.register_type is VirtualType.PAULI


def test_sample(rng):
    """Test the distribution is behaving sensibly."""
    assert UniformPauli(1).sample(1, rng).shape == (1, 1)
    assert UniformPauli(8).sample(1, rng).shape == (8, 1)
    assert UniformPauli(8).sample(100, rng).shape == (8, 100)
