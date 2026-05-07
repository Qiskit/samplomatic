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

"""PropagateParametricRzzNode"""

from collections.abc import Sequence

import numpy as np

from ...aliases import RegisterName, SubsystemIndex
from ...exceptions import SamplexRuntimeError
from ...virtual_registers import PauliRegister, VirtualType
from .evaluation_node import EvaluationNode

RZZ_COMMUTANT_PAULIS = np.array(
    [[0, 0], [0, 1], [1, 0], [1, 1], [2, 2], [2, 3], [3, 2], [3, 3]],
    dtype=PauliRegister.DTYPE,
)
"""The 8 two-qubit Paulis that commute with ZZ for any angle.

In symplectic ordering (I=0, Z=1, X=2, Y=3), these are the pairs where both
qubits are in {I,Z} or both are in {X,Y}.
"""

PARAMETRIC_RZZ_LOOKUP_TABLE = np.array(
    [
        [[0, 0], [0, 1], [-1, -1], [-1, -1]],
        [[1, 0], [1, 1], [-1, -1], [-1, -1]],
        [[-1, -1], [-1, -1], [2, 2], [2, 3]],
        [[-1, -1], [-1, -1], [3, 2], [3, 3]],
    ],
    dtype=np.intp,
)
"""Lookup table for propagating Paulis past a parametric RZZ gate.

Commutant elements (both in {I,Z} or both in {X,Y}) map to themselves.
Non-commutant elements map to -1 (sentinel) indicating an invalid state.
"""


class PropagateParametricRzzNode(EvaluationNode):
    """A node that guards Pauli propagation past a parametric RZZ gate.

    Only Paulis from the commutant of ZZ (those that commute with RZZ for any
    angle) are allowed through. Non-commutant Paulis trigger a runtime error.

    Args:
        register_name: The name of the Pauli register to propagate.
        subsystem_idxs: The subsystems in the register. The expected format is
            that of a collection of subsystems of the same size, i.e., that
            of a 2D array where the left-most axes is over subsystems and
            the right-most axes is over qubits.
    """

    def __init__(
        self,
        register_name: RegisterName,
        subsystem_idxs: Sequence[Sequence[SubsystemIndex]],
    ):
        self._subsystem_idxs = np.asarray(subsystem_idxs, dtype=np.intp)
        self._register_name = register_name

    @property
    def outgoing_register_type(self) -> VirtualType:
        return VirtualType.PAULI

    def evaluate(self, registers, *_):
        reg = registers[self._register_name]
        subsys = self._subsystem_idxs

        paulis_in = reg.virtual_gates[subsys]
        paulis_out = PARAMETRIC_RZZ_LOOKUP_TABLE[
            tuple(paulis_in[:, i] for i in range(subsys.shape[-1]))
        ]

        if np.any(paulis_out < 0):
            raise SamplexRuntimeError(
                "Pauli values are not in the commutant of RZZ after propagation."
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
            isinstance(other, PropagateParametricRzzNode)
            and np.array_equal(self._subsystem_idxs, other._subsystem_idxs)
            and self._register_name == other._register_name
        )

    def get_style(self):
        return (
            super()
            .get_style()
            .append_data("Operation", "'rzz' (parametric)")
            .append_data("Register Name", repr(self._register_name))
            .append_list_data("Subsystem Indices", self._subsystem_idxs.tolist())
        )
