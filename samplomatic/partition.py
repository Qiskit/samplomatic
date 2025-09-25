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

"""Partition"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Any, Generic, TypeVar

import numpy as np
from qiskit.circuit import Qubit

from .aliases import QubitIndex, SubsystemIndex
from .exceptions import BuildError

T = TypeVar("T", bound="Partition")
ElementT = TypeVar("ElementT")

__all__ = ["Partition"]


class Partition(Generic[ElementT]):
    """A partition of a sequence of elements into equally-sized, non-overlapping subsets.

    The :class:`~.Partition` class preserves the insertion order of the parts, as well as
    the order of the elements within the parts.

    Args:
        num_elements_per_part: How many elements each part must have.
        parts: ``None``, or the parts to initialize with.
    """

    def __init__(
        self, num_elements_per_part: int, parts: Iterable[tuple[ElementT, ...]] | None = None
    ):
        self.num_elements_per_part = num_elements_per_part
        self.all_elements: set[ElementT] = set()
        self._parts: dict[tuple[ElementT, ...], int] = {}

        for part in parts or []:
            self.add(part)

    def __contains__(self, part: tuple[ElementT, ...]) -> bool:
        return part in self._parts

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Partition) and self._parts == other._parts

    def __iter__(self) -> Iterator[tuple[ElementT, ...]]:
        return iter(self._parts)

    def __len__(self) -> int:
        return len(self._parts)

    def __repr__(self):
        return f"{type(self).__name__}({self.num_elements_per_part}, parts={list(self)})"

    def copy(self: T) -> T:
        """Copy this instance."""
        return Partition(self.num_elements_per_part, self._parts)

    def get_indices(self: T, other: T) -> np.ndarray[np.intp]:
        """Get the indices of the parts of ``other`` in this partition.

        Args:
            other: Some other partition whose elements are present in this partition.

        Returns:
            A list of indices indicating the position of the parts of ``other`` in this partition.
        """
        try:
            indices = [self._parts[part] for part in other]
        except KeyError as exc:
            raise BuildError(f"Could not find all indices of {other} in {self}.") from exc

        return np.array(indices, dtype=np.intp)

    def restrict(self, required: set[ElementT]) -> Partition:
        """Restrict to those parts with containment in the required set.

        Order is maintained of those remaining parts.
        """
        return Partition(
            self.num_elements_per_part,
            (part for part in self._parts if required.issuperset(part)),
        )

    def difference(self, subtracted: set[ElementT]) -> Partition:
        """Return the difference with respect to `subtracted`.

        Order is maintained of those remaining parts.
        """
        return Partition(
            self.num_elements_per_part,
            (part for part in self._parts if subtracted.isdisjoint(part)),
        )

    def overlaps_with(self, elements: Iterable[ElementT]) -> bool:
        """Whether any iterable of elements overlaps with these elements.

        Args:
            elements: Any iterable of elements to check against.

        Returns:
            Whether there is any overlap.
        """
        return not self.all_elements.isdisjoint(elements)

    def intersection(self, other: Partition, strict: bool = False) -> Partition:
        """Return a new partition that is the intersection with the other.

        The order of this partition is maintained, whereas the order of the other partition is
        irrelevant.

        Args:
            other: The other partition to take the intersection with.
            strict: Whether to error on partial overlaps.

        Raises:
            BuildError: If the two partitions have different numbers of elements per part.
            BuildError: If ``strict`` is ``True`` and ``other`` contains a part that partially
                overlaps with this partition.
        """
        if self.num_elements_per_part != other.num_elements_per_part:
            raise BuildError(
                f"Cannot take the intersection between {self} and {other} because they have "
                "different numbers of elements per part."
            )

        new_parts = []
        for self_part in self:
            if strict and other.overlaps_with(self_part) and self_part not in other:
                raise BuildError(
                    f"Cannot take intersection of {self} and {other} that partly overlap "
                    f"on elements {other.all_elements.intersection(self_part)}."
                )
            if self_part in other:
                new_parts.append(self_part)

        return Partition(self.num_elements_per_part, new_parts)

    def add(self, part: tuple[ElementT, ...]):
        """Add a new part to this partition.

        Args:
            part: The part to add.

        Raises:
            BuildError: If the part has the incorrect size.
            BuildError: If the part partially overlaps an existing part.
        """
        if len(part) != self.num_elements_per_part:
            raise BuildError("Subsystem size does not match.")
        if self.overlaps_with(part) and part not in self._parts:
            raise BuildError("Cannot act on partially overlapping parts.")

        self.all_elements.update(part)
        self._parts[part] = len(self._parts)

    @classmethod
    def from_elements(cls: type[T], elements: Iterable[ElementT]) -> T:
        """Construct a new instance in the special case that :attr:`~.num_elements_per_part` is one.

        Args:
            elements: The elements for each subsystem.

        Returns:
            A new partition where each part is an element from ``elements``.
        """
        return cls(1, [(element,) for element in elements])

    @classmethod
    def union(cls: type[T], *all_partitions: T) -> T:
        """Take the union of one or more partitions.

        Order is maintained with earlier ``all_partitions`` taking precedence.

        Args:
            all_partitions: The partitions to take the union of.

        Returns:
            The union of all the partitions.

        Raises:
            BuildError: If no partitions are given.
            BuildError: If the ``num_elements_per_part`` are incompatible.
            BuildError: If a partition partially overlaps another, or is reordered.
        """
        if not all_partitions:
            raise BuildError("At least one subsystem is required.")

        union = all_partitions[0].copy()
        num_elements_per_part = union.num_elements_per_part
        all_elements = union.all_elements
        union_parts = union._parts  # noqa: SLF001; we control the union, protected access is okay

        for partition in all_partitions[1:]:
            if partition.num_elements_per_part != num_elements_per_part:
                raise BuildError("Subsystem size does not match.")

            for part in partition:
                if part not in union_parts:
                    if not all_elements.isdisjoint(part):
                        raise BuildError(
                            "Cannot union when some partition are partially overlapping or "
                            f"reordered on {sorted(all_elements.intersection(part))}."
                        )
                    all_elements.update(part)
                    union_parts[part] = len(union_parts)

        return union


QubitPartition = Partition[Qubit]
"""A :class:`~.Partition` of a sequence of :class:`~.Qubit` objects."""

QubitIndicesPartition = Partition[QubitIndex]
"""A :class:`~.Partition` of a sequence of qubit indices."""

SubsystemIndicesPartition = Partition[SubsystemIndex]
"""A :class:`~.Partition` of a sequence of subsystem indices."""
