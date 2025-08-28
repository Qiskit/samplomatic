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

"""BasisTransformNode"""

from collections.abc import Iterable, Sequence
from typing import Generic, TypeVar

import numpy as np
import orjson
from qiskit.circuit.library import HGate, IGate, RYGate

from ...aliases import RegisterName, StrRef
from ...annotations import VirtualType
from ...virtual_registers import U2Register, VirtualRegister, virtual_register_from_json
from .sampling_node import SamplingNode

T = TypeVar("T")


class BasisChange(Generic[T]):
    """Represents a basis change.

    Args:
        alphabet: The symbols representing the basis elements.
        action: The basis change action for each symbol that transforms into the canonical basis.

    Raises:
        ValueError: If the number of symbols is not equal to the number of basis elements.
        ValueError: If the number of samples of the action is not one.
    """

    def __init__(self, alphabet: Iterable[T], action: VirtualRegister):
        self._alphabet = list(alphabet)
        self._action = action

        if len(self._alphabet) != self._action.num_subsystems:
            raise ValueError("The number of basis elements is not equal to the number of symbols.")
        if self._action.num_samples != 1:
            raise ValueError("Expected the number of samples of 'action' to be 1.")

        self._lookup = {
            character: transform[0]
            for character, transform in zip(self._alphabet, self._action.virtual_gates)
        }

    def to_json_dict(self) -> dict[str, str]:
        return {
            "alphabet": self.alphabet,
            "action": orjson.dumps(self.action.to_json_dict()).decode("utf-8"),
        }

    @classmethod
    def from_json_dict(cls, data: dict[str, str]) -> "BasisChange":
        return cls(
            data["alphabet"],
            virtual_register_from_json(orjson.loads(data["action"])),
        )

    @property
    def num_elements(self) -> int:
        """Number of elements."""
        return len(self._alphabet)

    @property
    def alphabet(self) -> list[T]:
        """Character symbols of basis elements.

        There should be one entry per entry in the virtual register.
        """
        return self._alphabet

    @property
    def action(self) -> VirtualRegister:
        """The basis change action for each symbol that transforms into the canonical basis.

        The register has ``num_samples==1``.
        """
        return self._action

    def get_transform(self, elements: Sequence[T]) -> VirtualRegister:
        """Return the transform for the basis change.

        Args:
            elements: The elements that specify the basis change.

        Returns:
            A virtual register containing the basis change.
        """
        return type(self.action)([[self._lookup[e]] for e in elements])


MEAS_PAULI_BASIS = BasisChange[np.uint8](
    [0, 1, 2, 3],
    U2Register(np.array([IGate(), HGate(), IGate(), RYGate(-np.pi / 2)]).reshape(4, 1, 2, 2)),
)
"""A basis change from Pauli eigenstates into the computational basis."""

PREP_PAULI_BASIS = BasisChange[np.uint8](
    [0, 1, 2, 3],
    U2Register(np.array([IGate(), HGate(), IGate(), RYGate(np.pi / 2)]).reshape(4, 1, 2, 2)),
)
"""A basis change from the computational basis into Pauli eigenstates."""


class BasisTransformNode(SamplingNode):
    """A node that instantiates a basis changing virtual register for a given measurement.

    Args:
        register_name: The name of the register to instantiate.
        basis_change: The basis change to implement.
        basis_ref: Unique identifier of the basis to use.
        num_subsystems: The number of subsystems this node generates gates for.
    """

    def __init__(
        self,
        register_name: RegisterName,
        basis_change: BasisChange,
        basis_ref: StrRef,
        num_subsystems: int,
    ):
        self._register_name = register_name
        self._basis_change = basis_change
        self._basis_ref = basis_ref
        self._num_subsystems = num_subsystems

    @property
    def outgoing_register_type(self) -> VirtualType:
        return self._basis_change.action.TYPE

    def instantiates(self):
        return {self._register_name: (self._num_subsystems, self._basis_change.action.TYPE)}

    def sample(self, registers, rng, inputs, num_randomizations):
        basis = inputs[self._basis_ref]
        registers[self._register_name] = self._basis_change.get_transform(basis)

    def _to_json_dict(self) -> dict[str, str]:
        return {
            "node_type": "0",
            "register_name": self._register_name,
            "basis_change": orjson.dumps(self._basis_change.to_json_dict()).decode("utf-8"),
            "basis_ref": self._basis_ref,
            "num_subsystems": str(self._num_subsystems),
        }

    @classmethod
    def _from_json_dict(cls, data: dict[str, str]) -> "BasisTransformNode":
        return cls(
            data["register_name"],
            BasisChange.from_json_dict(orjson.loads(data["basis_change"])),
            data["basis_ref"],
            int(data["num_subsystems"]),
        )

    def get_style(self):
        return (
            super()
            .get_style()
            .append_data("Register Name", repr(self._register_name))
            .append_data("Subsystems", repr(self._num_subsystems))
            .append_data("Basis Reference", repr(self._basis_ref))
        )
