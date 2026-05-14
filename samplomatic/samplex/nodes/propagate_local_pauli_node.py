# This code is a Qiskit project.
#
# (C) Copyright IBM 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""PropagateLocalPauliNode"""

from collections.abc import Sequence

import numpy as np

from ...aliases import RegisterName, SubsystemIndex
from ...exceptions import SamplexRuntimeError
from ...virtual_registers import VirtualType
from .evaluation_node import EvaluationNode

_COMMUTANT_TABLES = {
    "rzz": np.array(
        [
            [[0, 0], [0, 1], [-1, -1], [-1, -1]],
            [[1, 0], [1, 1], [-1, -1], [-1, -1]],
            [[-1, -1], [-1, -1], [2, 2], [2, 3]],
            [[-1, -1], [-1, -1], [3, 2], [3, 3]],
        ],
        dtype=np.intp,
    ),
}


class PropagateLocalPauliNode(EvaluationNode):
    """A node that propagates a Pauli register past a gate.

    Only Paulis from the commutant of the gate generators (those that commute
    with the gate for any angle) are allowed through. Non-commutant Paulis
    trigger a runtime error.

    Args:
        register_name: The name of the Pauli register to propagate.
        subsystem_idxs: The subsystems in the register specified as a 2D array where the left-most
            axes is over subsystems and the right-most axes is over indices in the subsystem.
        op_name: The name of the gate operation.
    """

    def __init__(
        self,
        op_name: str,
        register_name: RegisterName,
        subsystem_idxs: Sequence[Sequence[SubsystemIndex]],
        *,
        lookup_table: np.ndarray | None = None,
    ):
        if lookup_table is not None:
            self._table = lookup_table
        else:
            if op_name not in _COMMUTANT_TABLES:
                raise ValueError(
                    f"Unsupported operation {op_name!r}. "
                    f"Supported operations: {sorted(_COMMUTANT_TABLES)}."
                )
            self._table = _COMMUTANT_TABLES[op_name]
        self._subsystem_idxs = np.asarray(subsystem_idxs, dtype=np.intp)
        self._register_name = register_name
        self._op_name = op_name

    @property
    def outgoing_register_type(self) -> VirtualType:
        return VirtualType.PAULI

    def evaluate(self, registers, *_):
        reg = registers[self._register_name]
        subsys = self._subsystem_idxs

        paulis_in = reg.virtual_gates[subsys]
        paulis_out = self._table[tuple(paulis_in[:, i] for i in range(subsys.shape[-1]))]

        if np.any(paulis_out < 0):
            raise SamplexRuntimeError(
                f"Pauli values not in the commutant of {self._op_name!r} cannot be propagated."
            )

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

    def __eq__(self, other):
        return (
            isinstance(other, PropagateLocalPauliNode)
            and self._op_name == other._op_name
            and np.array_equal(self._subsystem_idxs, other._subsystem_idxs)
            and self._register_name == other._register_name
        )

    def get_style(self):
        return (
            super()
            .get_style()
            .append_data("Operation", f"{self._op_name!r}")
            .append_data("Register Name", repr(self._register_name))
            .append_list_data("Subsystem Indices", self._subsystem_idxs.tolist())
        )
