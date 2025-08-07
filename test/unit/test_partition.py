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


import numpy as np
import pytest

from samplomatic.exceptions import BuildError
from samplomatic.partition import Partition


def test_construction():
    """Test construction and attributes."""
    partition = Partition(2)
    assert partition.num_elements_per_part == 2
    assert partition.all_elements == set()

    partition = Partition(1, [(0,), (2,)])
    assert partition.num_elements_per_part == 1
    assert partition.all_elements == {0, 2}


def test_contains():
    """Test the containment dunder."""
    partition = Partition(2, [(0, 1), (2, 3)])
    assert (0, 1) in partition
    assert (2, 3) in partition
    assert (1, 2) not in partition
    assert (1, 0) not in partition


def test_insertion_ordered():
    """Test the container maintains insertion order."""
    partition = Partition(2, [(6, 7), (2, 3)])
    partition.add((1, 0))
    assert list(partition) == [(6, 7), (2, 3), (1, 0)]


def test_iteration():
    """Test the iteration dunder."""
    partition = Partition(2, [(0, 1), (2, 3)])
    assert set(partition) == {(0, 1), (2, 3)}


def test_len():
    """Test the length dunder."""
    partition = Partition(2, [(0, 1), (2, 3)])
    assert len(partition) == 2


def test_overlaps_with():
    """Test overlaps_with()."""
    partition = Partition(2, [(0, 1), (2, 3)])
    assert partition.overlaps_with([1])
    assert partition.overlaps_with(iter([1, 18]))
    assert partition.overlaps_with([1, 0])

    assert not partition.overlaps_with([])
    assert not partition.overlaps_with([5, 8])
    assert not partition.overlaps_with(iter([5, 8]))


def test_add():
    """Test add()."""
    partition = Partition(2, [(0, 1), (2, 3)])
    assert set(partition) == {(0, 1), (2, 3)}

    partition.add((0, 1))
    assert set(partition) == {(0, 1), (2, 3)}

    partition.add((4, 5))
    assert set(partition) == {(0, 1), (2, 3), (4, 5)}


def test_add_raises():
    """Test add() raises."""
    partition = Partition(2, [(0, 1), (2, 3)])
    with pytest.raises(BuildError, match="size does not match"):
        partition.add((4,))
    assert set(partition) == {(0, 1), (2, 3)}

    with pytest.raises(BuildError, match="partially overlapping parts"):
        partition.add((3, 4))
    assert set(partition) == {(0, 1), (2, 3)}


def test_get_indices():
    """Test the get_indices method."""
    partition = Partition(2, [(0, 1), (2, 3), (4, 5)])
    assert np.array_equal(partition.get_indices(partition), np.array([0, 1, 2]))

    other = Partition(2, [(2, 3), (0, 1), (4, 5)])
    assert np.array_equal(partition.get_indices(other), np.array([1, 0, 2]))

    other = Partition(2, [(4, 5), (0, 1)])
    assert np.array_equal(partition.get_indices(other), np.array([2, 0]))


def test_get_indices_raises():
    """Test that get_indices raises."""
    partition = Partition(2, [(0, 1), (2, 3), (4, 5)])

    with pytest.raises(BuildError, match="Could not find"):
        partition.get_indices(Partition(2, [(1, 2)]))

    with pytest.raises(BuildError, match="Could not find"):
        partition.get_indices(Partition(2, [(8, 9)]))


def test_copy():
    """Test the copy method."""
    partition = Partition(2, [(0, 1), (2, 3)])
    copy = partition.copy()

    assert list(partition) == list(copy)
    assert partition is not copy

    partition.add((4, 5))
    assert (4, 5) in partition and (4, 5) not in copy


def test_from_elements():
    """Test the from_elements constructor."""
    partition = Partition.from_elements([2, 3, 5, 7, 11])
    assert partition.num_elements_per_part == 1
    assert list(partition) == [(2,), (3,), (5,), (7,), (11,)]


def test_union():
    """Test the union method."""
    partition0 = Partition(2, [(0, 1), (2, 3)])
    partition1 = Partition(2, [(2, 3), (4, 5)])
    partition2 = Partition(2, [(6, 7)])

    union = Partition.union(partition0, partition1, partition2)
    assert set(union) == set(partition0) | set(partition1) | set(partition2)


def test_union_raises():
    """Test that the union method raises when expected."""
    with pytest.raises(BuildError, match="At least one subsystem is required"):
        Partition.union()

    partition = Partition(2, [(0, 1), (2, 3)])

    with pytest.raises(BuildError, match="Subsystem size does not match"):
        Partition.union(partition, Partition(3, [(2, 3, 4)]))

    with pytest.raises(BuildError, match=r"partially overlapping or reordered on \[1\]"):
        Partition.union(partition, Partition(2, [(4, 5), (1, 10)]))

    with pytest.raises(BuildError, match=r"partially overlapping or reordered on \[0, 1\]"):
        Partition.union(partition, Partition(2, [(4, 5), (1, 0)]))
