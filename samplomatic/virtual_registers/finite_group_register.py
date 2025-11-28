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

"""FiniteGroupRegister"""

import abc

import numpy as np

from ..aliases import SubsystemIndex
from ..exceptions import VirtualGateError
from .group_register import GroupRegister


class FiniteGroupRegister(GroupRegister):
    """A virtual register whose elements form a finite group.

    The elements of the group are enumerated and act as indices of the the :attr:`~lookup_table` and
    :attr:`~inverse_table`. By taking the appropriate slices, this implements the group operation
    and the inverse.
    """

    @property
    @abc.abstractmethod
    def lookup_table(self) -> np.ndarray:
        """The lookup table for the group operation."""

    @property
    @abc.abstractmethod
    def inverse_table(self) -> np.ndarray:
        """The lookup table for the inverse."""

    @property
    def num_elements(self) -> int:
        """The number of distinct elements in the group."""
        return len(self.lookup_table)

    def invert(self):
        return type(self)(self.inverse_table[self.virtual_gates])

    def multiply(self, other, subsystem_idxs: list[SubsystemIndex] | slice = slice(None)):
        try:
            return type(self)(
                self.lookup_table[self._array[subsystem_idxs, :], other.virtual_gates]
            )
        except (ValueError, IndexError) as exc:
            raise VirtualGateError(
                f"Register {self} and {other} have incompatible shapes or types, "
                f"given subsystem_idxs {subsystem_idxs}."
            ) from exc

    def inplace_multiply(self, other, subsystem_idxs: list[SubsystemIndex] | slice = slice(None)):
        try:
            self._array[subsystem_idxs, :] = self.lookup_table[
                self._array[subsystem_idxs, :], other.virtual_gates
            ]
        except (ValueError, IndexError) as exc:
            raise VirtualGateError(
                f"Register {self} and {other} have incompatible shapes or types, "
                f"given subsystem_idxs {subsystem_idxs}."
            ) from exc

    def left_multiply(self, other, subsystem_idxs: list[SubsystemIndex] | slice = slice(None)):
        try:
            return type(self)(
                self.lookup_table[other.virtual_gates, self._array[subsystem_idxs, :]]
            )
        except (ValueError, IndexError) as exc:
            raise VirtualGateError(
                f"Register {self} and {other} have incompatible shapes or types, "
                f"given subsystem_idxs {subsystem_idxs}."
            ) from exc

    def left_inplace_multiply(
        self, other, subsystem_idxs: list[SubsystemIndex] | slice = slice(None)
    ):
        try:
            self._array[subsystem_idxs, :] = self.lookup_table[
                other.virtual_gates, self._array[subsystem_idxs, :]
            ]
        except (ValueError, IndexError) as exc:
            raise VirtualGateError(
                f"Register {self} and {other} have incompatible shapes or types, "
                f"given subsystem_idxs {subsystem_idxs}."
            ) from exc
