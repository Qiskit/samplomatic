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
from typing import Any

from qiskit.quantum_info import QubitSparsePauliList


@dataclass
class NoiseModelRequirement:
    """A class that represents a noise model required for sampling."""

    noise_ref: str
    """A unique reference to this handle."""

    num_qubits: int
    """The number of qubits this model acts on."""

    noise_modifiers: set[str] = field(default_factory=set)
    """The set of modifiers that act on this noise model."""

    def _to_json_dict(self) -> dict[str, str]:
        return {
            "noise_ref": self.noise_ref,
            "num_qubits": self.num_qubits,
            "noise_modifiers": [modifier for modifier in self.noise_modifiers],
        }

    @classmethod
    def _from_json(cls, data: dict[str, Any]) -> "NoiseModelRequirement":
        data["noise_modifiers"] = set(data["noise_modifiers"])
        return cls(**data)

    def validate_noise_model(self, value: QubitSparsePauliList):
        if self.num_qubits != value.num_qubits:
            raise ValueError(
                f"Noise model for '{self.noise_ref}' is expected to act on '{self.num_qubits}` "
                f"systems, not '{value.num_qubits}'."
            )
