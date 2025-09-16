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

"""GroupRegister"""

from __future__ import annotations

import abc
from typing import TypeVar

from ..aliases import SubsystemIndex
from .virtual_register import VirtualRegister

T = TypeVar("T")


class GroupRegister(VirtualRegister):
    """A virtual register whose elements form a group."""

    @abc.abstractmethod
    def invert(self: T) -> T:
        """Return a new virtual register that inverts each virtual gate."""

    @abc.abstractmethod
    def multiply(
        self: T, other: T, subsystem_idxs: list[SubsystemIndex] | slice = slice(None)
    ) -> T:
        """Multiply each virtual gate with the corresponding element of ``other``.

        Args:
            other: Another virtual register of the same type.
            subsystem_idxs: The indices of the subsystems to multiply, in self.

        Returns:
            A new virtual register of the same type.

        Raises:
            VirtualGateError: When the shapes do not match.
        """

    @abc.abstractmethod
    def inplace_multiply(
        self: T, other: T, subsystem_idxs: list[SubsystemIndex] | slice = slice(None)
    ):
        """Inplace-multiply each virtual gate with the corresponding element of ``other``.

        Args:
            other: Another virtual register of the same type.
            subsystem_idxs: The indices of the subsystems to multiply, in self.

        Raises:
            VirtualGateError: When the shapes do not match.
        """

    def left_multiply(
        self: T, other: T, subsystem_idxs: list[SubsystemIndex] | slice = slice(None)
    ) -> T:
        """Left multiply each virtual gate with the corresponding element of ``other``.

        Args:
            other: Another virtual register of the same type.
            subsystem_idxs: The indices of the subsystems to multiply, in self.

        Returns:
            A new virtual register of the same type.

        Raises:
            VirtualGateError: When the shapes do not match.
        """
        return self.multiply(other, subsystem_idxs)

    def left_inplace_multiply(
        self: T, other: T, subsystem_idxs: list[SubsystemIndex] | slice = slice(None)
    ):
        """Left inplace-multiply each virtual gate with the corresponding element of ``other``.

        Args:
            other: Another virtual register of the same type.
            subsystem_idxs: The indices of the subsystems to multiply, in self.

        Raises:
            VirtualGateError: When the shapes do not match.
        """
        self.inplace_multiply(other, subsystem_idxs)
