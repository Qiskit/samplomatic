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

"""Synth"""

import abc
from collections.abc import Iterable
from typing import Any, Generic, TypeVar

import numpy as np

from ..annotations import VirtualType
from ..virtual_registers import VirtualRegister

InstructionT = TypeVar("InstructionT")
ParameterT = TypeVar("ParameterT")
QubitT = TypeVar("QubitT")


class Synth(Generic[QubitT, ParameterT, InstructionT]):
    """Base class for synthesizers."""

    num_qubits: int = 1
    num_params: int = 0
    compatible_register_types: frozenset[VirtualType] = frozenset()

    def __eq__(self, other: Any):
        return type(self) is type(other)

    def __repr__(self):
        return (
            f"{type(self).__name__}(<num_qubits_per_subsystem={self.num_qubits}, "
            f"num_params_per_subsystem={self.num_params}>)"
        )

    @abc.abstractmethod
    def make_template(
        self, qubits: list[QubitT], params: Iterable[ParameterT]
    ) -> Iterable[InstructionT]:
        """Return a parametric template that can synthesize gates.

        Args:
            qubits: The qubits for which to make the template.
            params: The ordered parameters to use while making the template.

        Yields:
            Instructions that implement the template.

        Raises:
            SynthError: When there is a problem synthesizing.
        """

    @abc.abstractmethod
    def generate_template_values(self, register: VirtualRegister) -> np.ndarray:
        """Generate parameter values for all gates of the register valid for this synth's template.

        Args:
            register: The data register containing the virtual gates to generate template parameter
                values for.

        Returns:
            An array of shape ``(register.num_subsystems, register.num_samples, num_params)``.

        Raises:
            SynthError: If the provided virtual register type is incompatible with this synth.
        """
