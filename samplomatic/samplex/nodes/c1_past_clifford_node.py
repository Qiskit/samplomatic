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

"""C1PastCliffordNode"""

from collections.abc import Sequence

import numpy as np

from ...aliases import OperationName, RegisterName, SubsystemIndex
from ...exceptions import SamplexBuildError, SamplexRuntimeError
from ...tables.local_c1_tables import C1_PAST_CLIFFORD_LOOKUP_TABLES
from ...virtual_registers import VirtualType
from .evaluation_node import EvaluationNode

C1_PAST_CLIFFORD_INVARIANTS = frozenset({"id"})
"""Set of gates which a C1 element is invariant under conjugation with."""


class C1PastCliffordNode(EvaluationNode):
    """A node that propagates a C1 register past a Clifford gate.

    Args:
        op_name: The name of the Clifford gate.
        register_name: The name of the C1 register to propagate.
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
            self._lookup_table = C1_PAST_CLIFFORD_LOOKUP_TABLES[op_name]
        except KeyError:
            supported_gates = list(C1_PAST_CLIFFORD_LOOKUP_TABLES)
            raise SamplexBuildError(f"Expected one of {supported_gates}, found {op_name}.")

        self._op_name = op_name
        self._subsystem_idxs = np.asarray(subsystem_idxs, dtype=np.intp)
        self._register_name = register_name

    @property
    def outgoing_register_type(self) -> VirtualType:
        return VirtualType.C1

    def evaluate(self, registers, *_):
        reg = registers[self._register_name]
        subsys = self._subsystem_idxs

        c1_in = reg.virtual_gates[subsys]
        c1_out = self._lookup_table[tuple(c1_in[:, i] for i in range(subsys.shape[-1]))]

        if np.any(c1_out < 0):
            raise SamplexRuntimeError(
                f"C1 values did not remain local after conjugation by {self._op_name!r}."
            )

        reg.virtual_gates[subsys] = np.transpose(c1_out, (0, 2, 1))

    def reads_from(self):
        return {
            self._register_name: (
                set(s for tup in self._subsystem_idxs for s in tup),
                VirtualType.C1,
            )
        }

    def writes_to(self):
        return {
            self._register_name: (
                set(s for tup in self._subsystem_idxs for s in tup),
                VirtualType.C1,
            )
        }

    def __eq__(self, other):
        return (
            isinstance(other, C1PastCliffordNode)
            and self._op_name == other._op_name
            and np.array_equal(self._subsystem_idxs, other._subsystem_idxs)
            and self._register_name == other._register_name
        )

    def get_style(self):
        return (
            super()
            .get_style()
            .append_data("Operation", repr(self._op_name))
            .append_data("Register Name", repr(self._register_name))
            .append_data("Subsystem Indices", self._subsystem_idxs.tolist())
        )
