# This code is a Qiskit project.
#
# (C) Copyright IBM 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Test the UniformLocalC1 distribution"""

import numpy as np
import pytest

from samplomatic.distributions import HaarU2, UniformLocalC1
from samplomatic.samplex.nodes.c1_past_clifford_node import C1_PAST_CLIFFORD_LOOKUP_TABLES
from samplomatic.virtual_registers import VirtualType


def test_attributes():
    """Test basic attributes of the distribution class."""
    distribution = UniformLocalC1(2, "cx")

    assert distribution.num_subsystems == 2
    assert distribution.register_type is VirtualType.C1


def test_equality():
    """Test equality."""
    distribution = UniformLocalC1(2, "cx")
    assert distribution == distribution
    assert distribution == UniformLocalC1(2, "cx")
    assert distribution != HaarU2(2)
    assert distribution != UniformLocalC1(4, "cx")
    assert distribution != UniformLocalC1(2, "cz")


def test_sample(rng):
    """Test the distribution is behaving sensibly."""
    assert UniformLocalC1(2, "cx").sample(1, rng).shape == (2, 1)
    assert UniformLocalC1(2, "cx").sample(100, rng).shape == (2, 100)
    assert UniformLocalC1(4, "cz").sample(1, rng).shape == (4, 1)
    assert UniformLocalC1(4, "cz").sample(50, rng).shape == (4, 50)

    assert UniformLocalC1(2, "cx").sample(1, rng).virtual_gates.shape == (2, 1)
    assert UniformLocalC1(2, "cx").sample(100, rng).virtual_gates.shape == (2, 100)


@pytest.mark.parametrize("gate", ["cx", "cz", "ecr"])
def test_samples_are_local(rng, gate):
    """Test that every sampled pair stays local under conjugation by the gate."""
    table = C1_PAST_CLIFFORD_LOOKUP_TABLES[gate]
    samples = UniformLocalC1(2, gate).sample(1000, rng)
    vg = samples.virtual_gates

    for i in range(vg.shape[1]):
        result = table[vg[0, i], vg[1, i]]
        assert np.all(result >= 0), f"Pair ({vg[0, i]}, {vg[1, i]}) is not local for {gate}."


@pytest.mark.parametrize("gate", ["cx", "cz", "ecr"])
def test_multiple_pairs_are_local(rng, gate):
    """Test locality when num_subsystems > 2 (multiple independent pairs)."""
    table = C1_PAST_CLIFFORD_LOOKUP_TABLES[gate]
    samples = UniformLocalC1(6, gate).sample(200, rng)
    vg = samples.virtual_gates

    for pair_idx in range(3):
        c0 = vg[2 * pair_idx]
        c1 = vg[2 * pair_idx + 1]
        for i in range(vg.shape[1]):
            result = table[c0[i], c1[i]]
            assert np.all(result >= 0)


@pytest.mark.parametrize("gate", ["cx", "cz", "ecr"])
def test_samples_cover_all_valid_pairs(rng, gate):
    """Test that sampling covers the full support given enough draws."""
    table = C1_PAST_CLIFFORD_LOOKUP_TABLES[gate]
    expected_valid = set(map(tuple, np.argwhere(np.all(table >= 0, axis=-1))))

    samples = UniformLocalC1(2, gate).sample(100_000, rng)
    vg = samples.virtual_gates
    observed = {(int(vg[0, i]), int(vg[1, i])) for i in range(vg.shape[1])}

    assert observed == expected_valid


def test_odd_num_subsystems_raises():
    """Test that odd num_subsystems raises ValueError."""
    with pytest.raises(ValueError, match="num_subsystems must be even"):
        UniformLocalC1(3, "cx")


def test_unknown_gate_raises():
    """Test that an unknown gate name raises ValueError."""
    with pytest.raises(ValueError, match="Unknown gate"):
        UniformLocalC1(2, "not_a_gate")


def test_one_qubit_gate_raises():
    """Test that a one-qubit gate raises ValueError."""
    with pytest.raises(ValueError, match="not a two-qubit gate"):
        UniformLocalC1(2, "h")
