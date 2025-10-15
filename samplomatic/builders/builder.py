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

SamplexT = TypeVar("SamplexT")
TemplateT = TypeVar("TemplateT")


class Builder(Generic[TemplateT, SamplexT], abc.ABC):
    """Generic abstraction for parsing a :class:`~.QuantumCircuit` scope."""

    def __init__(self):
        self._samplex_state = None
        self._template_state = None

    def set_samplex_state(self, samplex_state: SamplexT) -> Self:
        """Set the current samplex state of the builder.

        Args:
            samplex_state: The new state.

        Returns:
            A reference to this builder.
        """
        self._samplex_state = samplex_state
        return self

    def set_template_state(self, template_state: TemplateT) -> Self:
        """Set the current template state of the builder.

        Args:
            template_state: The new state.

        Returns:
            A reference to this builder.
        """
        self._template_state = template_state
        return self

    @property
    def samplex_state(self) -> SamplexT:
        """The current samplex state of the builder."""
        if self._samplex_state is None:
            raise BuildError(
                f"Attempted to access the samplex state of {self} before it has been set."
            )
        return self._samplex_state

    @property
    def template_state(self) -> TemplateT:
        """The current template state of the builder."""
        if self._template_state is None:
            raise BuildError(
                f"Attempted to access the template state of {self} before it has been set."
            )
        return self._template_state

    @abc.abstractmethod
    def parse(self, instr: CircuitInstruction):
        """Parse a single circuit instruction."""

    @abc.abstractmethod
    def lhs(self):
        """Perform some action before the current scope's stream is iterated."""

    @abc.abstractmethod
    def rhs(self):
        """Perform some action after the current scope's stream is iterated."""
