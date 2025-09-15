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

"""PauliPastCliffordNode"""

from collections.abc import Sequence

import numpy as np

from ...aliases import OperationName, RegisterName, SubsystemIndex
from ...annotations import VirtualType
from ...exceptions import SamplexBuildError
from ...utils.serialization import array_from_json, array_to_json
from .evaluation_node import EvaluationNode

PAULI_PAST_CLIFFORD_LOOKUP_TABLES = {
    "h": np.array([[0], [2], [1], [3]], dtype=np.intp),
    "cx": np.array(
        [
            [[0, 0], [1, 1], [0, 2], [1, 3]],
            [[1, 0], [0, 1], [1, 2], [0, 3]],
            [[2, 2], [3, 3], [2, 0], [3, 1]],
            [[3, 2], [2, 3], [3, 0], [2, 1]],
        ],
        dtype=np.intp,
    ),
    "cz": np.array(
        [
            [[0, 0], [0, 1], [1, 2], [1, 3]],
            [[1, 0], [1, 1], [0, 2], [0, 3]],
            [[2, 1], [2, 0], [3, 3], [3, 2]],
            [[3, 1], [3, 0], [2, 3], [2, 2]],
        ],
        dtype=np.intp,
    ),
    "ecr": np.array(
        [
            [[0, 0], [1, 3], [0, 2], [1, 1]],
            [[1, 0], [0, 3], [1, 2], [0, 1]],
            [[3, 2], [2, 1], [3, 0], [2, 3]],
            [[2, 2], [3, 1], [2, 0], [3, 3]],
        ],
        dtype=np.intp,
    ),
}
"""Lookup tables for computing the conjugation of Pauli operators by Clifford gates.

Single-qubit Pauli operators are indexed as in :class:`~.PauliRegister`\\s. Computing the
conjugation of a Pauli by a Clifford can be done via slicing. For example,
``PAULI_PAST_CLIFFORD_LOOKUP_TABLES["h"][i]`` gives the conjugation of a Pauli ``i`` by
an H gate, while ``PAULI_PAST_CLIFFORD_LOOKUP_TABLES["cx"][i, j]`` gives that of Paulis
``i`` and ``j`` by CX.
"""

PAULI_PAST_CLIFFORD_INVARIANTS = {"x", "z", "y", "id"}
"""Set of gates which a Pauli is invariant (up to a sign) under conjugation with."""


class PauliPastCliffordNode(EvaluationNode):
    """A node that propagates a Pauli register past a Clifford gate.

    Args:
        op_name: The name of the Clifford gate.
        register_name: The name of the Pauli register to propagate.
        subsystem_idxs: The subsystems in the register. The expected format is
            that of a collection of subsystems of the same size, i.e., that
            of a 2D array where the left-most axes is over subsystems and
            the right-most axes is over qubits.
    """

    def __init__(
        self,
        op_name: OperationName,
        register_name: RegisterName,
        subsystem_idxs: Sequence[Sequence[SubsystemIndex]],
    ):
        try:
            self._lookup_table = PAULI_PAST_CLIFFORD_LOOKUP_TABLES[op_name]
        except KeyError:
            supported_gates = list(PAULI_PAST_CLIFFORD_LOOKUP_TABLES)
            raise SamplexBuildError(f"Expected one of {supported_gates}, found {op_name}.")

        self._op_name = op_name
        self._subsystem_idxs = np.asarray(subsystem_idxs, dtype=np.intp)
        self._register_name = register_name

    def _to_json_dict(self) -> dict[str, str]:
        return {
            "node_type": "7",
            "op_name": self._op_name,
            "subsystem_idxs": array_to_json(self._subsystem_idxs),
            "register_name": self._register_name,
        }

    @classmethod
    def _from_json_dict(cls, data: dict[str, str]) -> "PauliPastCliffordNode":
        return cls(
            data["op_name"],
            data["register_name"],
            array_from_json(data["subsystem_idxs"]),
        )

    @property
    def outgoing_register_type(self) -> VirtualType:
        return VirtualType.PAULI

    def evaluate(self, registers, *_):
        reg = registers[self._register_name]
        subsys = self._subsystem_idxs

        paulis_in = reg.virtual_gates[subsys]
        paulis_out = self._lookup_table[tuple(paulis_in[:, i] for i in range(subsys.shape[-1]))]
        reg.virtual_gates[subsys] = np.transpose(paulis_out, (0, 2, 1))

    def reads_from(self):
        return {
            self._register_name: (
                set(s for tup in self._subsystem_idxs for s in tup),
                VirtualType.PAULI,
            )
        }

    def writes_to(self):
        return {
            self._register_name: (
                set(s for tup in self._subsystem_idxs for s in tup),
                VirtualType.PAULI,
            )
        }

    def get_style(self):
        return (
            super()
            .get_style()
            .append_data("Operation", repr(self._op_name))
            .append_data("Register Name", repr(self._register_name))
            .append_data("Subsystem Indices", self._subsystem_idxs.tolist())
        )
