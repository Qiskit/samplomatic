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

"""Builder"""

import abc
from typing import Generic, TypeVar

from ..aliases import CircuitInstruction, Self
from ..exceptions import BuildError

StateT = TypeVar("StateT")
OutT = TypeVar("OutT")


class Builder(Generic[StateT, OutT], abc.ABC):
    """Generic abstraction for parsing a :class:`~.QuantumCircuit` scope."""

    def __init__(self):
        self._state = None

    def set_state(self, state: StateT) -> Self:
        """Set the current state of the builder.

        Args:
            state: The new state.

        Returns:
            A reference to this builder.
        """
        self._state = state
        return self

    @property
    def state(self) -> StateT:
        """The current state of the builder."""
        if self._state is None:
            raise BuildError(f"Attempted to access the state of {self} before it has been set.")
        return self._state

    @abc.abstractmethod
    def parse(self, instr: CircuitInstruction, *args) -> OutT:
        """Parse a single circuit instruction."""

    @abc.abstractmethod
    def lhs(self, *args) -> OutT:
        """Perform some action before the current scope's stream is iterated.

        Args:
            args: Arguments required at the LHS boundary.

        Returns:
            Information about the boundary.
        """

    @abc.abstractmethod
    def rhs(self, *args) -> OutT:
        """Perform some action after the current scope's stream is iterated.

        Args:
            args: Arguments required at the LHS boundary.

        Returns:
            Information about the boundary.
        """
