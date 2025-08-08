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

"""Test the HaarU2 distribution"""

import numpy as np

from samplomatic.annotations import VirtualType
from samplomatic.distributions import HaarU2


def test_attributes():
    """Test basic attributes of the distribution class."""
    distribution = HaarU2(13)

    assert distribution.num_subsystems == 13
    assert distribution.register_type is VirtualType.U2


def test_sample_shape(rng):
    """Test the distribution shape is behaving sensibly."""
    assert HaarU2(1).sample(1, rng).shape == (1, 1)
    assert HaarU2(8).sample(1, rng).shape == (8, 1)
    assert HaarU2(8).sample(100, rng).shape == (8, 100)

    assert HaarU2(1).sample(1, rng).virtual_gates.shape == (1, 1, 2, 2)
    assert HaarU2(8).sample(1, rng).virtual_gates.shape == (8, 1, 2, 2)
    assert HaarU2(8).sample(100, rng).virtual_gates.shape == (8, 100, 2, 2)


def test_samples_are_unitary(rng):
    """Test the distribution produces unitary samples."""
    gates = HaarU2(11).sample(7, rng).virtual_gates
    products = np.matmul(gates.transpose(0, 1, 3, 2).conj(), gates)
    assert np.allclose(products, np.eye(2))


def test_sample_correctness(rng):
    """Test the distribution has okay-looking eigenvalues and frame potential."""
    gates = HaarU2(1).sample(num_samples := 1000, rng).virtual_gates

    eigenvalues = np.linalg.eigvals(gates)
    assert np.allclose(eigenvalues.mean(axis=1), 0, atol=0.1)

    # check that samples are consistent with unitary 2-design, Thm 2 of
    # https://arxiv.org/pdf/quant-ph/0611002
    traces = gates.reshape(-1, 4) @ gates.transpose(2, 3, 0, 1).reshape(4, -1).conj()
    frame_potential = np.sum(np.abs(traces) ** 4) / num_samples**2
    assert np.isclose(frame_potential, 2, atol=0.1)
