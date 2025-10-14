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

"""NoiseRequirement"""

from dataclasses import dataclass, field
from typing import Any

from qiskit.quantum_info import QubitSparsePauliList


@dataclass
class NoiseRequirement:
    """A class that represents a required noise for sampling."""

    noise_ref: str
    """A unique reference to this requirement."""

    num_qubits: int
    """The number of qubits this requirement expects the noise to act on."""

    noise_modifiers: set[str] = field(default_factory=set)
    """The set of modifiers that are associated with this requirement."""

    def _to_json_dict(self) -> dict[str, str]:
        return {
            "noise_ref": self.noise_ref,
            "num_qubits": self.num_qubits,
            "noise_modifiers": [modifier for modifier in self.noise_modifiers],
        }

    @classmethod
    def _from_json(cls, data: dict[str, Any]) -> "NoiseRequirement":
        data["noise_modifiers"] = set(data["noise_modifiers"])
        return cls(**data)

    def validate_num_qubits(self, paulis: QubitSparsePauliList):
        """Validate the number of qubits of 'paulis' against this requirement.

        Args:
            paulis: The Paulis to validate.

        Raises:
            ValueError: If 'paulis.num_qubits' is not equal to 'num_qubits' of this instance.
        """
        if self.num_qubits != paulis.num_qubits:
            raise ValueError(
                f"The Paullis for '{self.noise_ref}' are expected to act on '{self.num_qubits}` "
                f"systems, received '{paulis.num_qubits}'."
            )
