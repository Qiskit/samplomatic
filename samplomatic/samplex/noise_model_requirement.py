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

"""NoiseModelRequirement"""

from dataclasses import dataclass, field

from qiskit.quantum_info import QubitSparsePauliList


@dataclass
class NoiseModelRequirement:
    """A class that represents a noise model required for sampling."""

    noise_ref: str
    """A unique reference to this handle."""

    num_qubits: int
    """The number of qubits this model acts on."""

    noise_modifiers: set = field(default=set)
    """The set of modifiers that act on this noise model."""

    paulis: QubitSparsePauliList | None = field(default=None)
    """The terms present in this model."""

    def _validate_noise_model(self, value: QubitSparsePauliList | None):
        if value is not None and self.num_qubits != value.num_qubits:
            raise ValueError(
                f"Noise model for '{self.noise_ref}' is expected to act on '{self.num_qubits}` "
                f"systems, not '{value.num_qubits}'."
            )

    def __setattr__(self, name, value):
        if name == "paulis":
            self._validate_noise_model(value)
        super().__setattr__(name, value)
