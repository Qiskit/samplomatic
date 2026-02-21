# This code is a Qiskit project.
#
# (C) Copyright IBM 2025, 2026.
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
from qiskit.quantum_info import Clifford

from ...aliases import OperationName, RegisterName, SubsystemIndex
from ...exceptions import SamplexBuildError, SamplexRuntimeError
from ...virtual_registers import VirtualType
from ...virtual_registers.c1_register import C1_TO_TABLEAU
from .evaluation_node import EvaluationNode


def _build_c1_tableau_map():
    """Return a dict mapping tableau bytes to C1 index."""
    return {C1_TO_TABLEAU[i].tobytes(): i for i in range(24)}


def _compute_2q_table(gate_name):
    """Compute the 2q conjugation table for a named Clifford gate.

    For each pair ``(c0, c1)`` of C1 indices, conjugate ``C1[c1] ⊗ C1[c0]`` by the gate.
    If the result factorizes as ``C1[c0'] ⊗ C1[c1']``, store the indices; otherwise store
    the sentinel value ``-1``.
    """
    from qiskit.circuit.library import CXGate, CZGate, ECRGate

    gates = {"cx": CXGate, "cz": CZGate, "ecr": ECRGate}
    gate_cliff = Clifford(gates[gate_name]())
    gate_inv = gate_cliff.adjoint()
    tableau_map = _build_c1_tableau_map()
    table = np.full((24, 24, 2), -1, dtype=np.intp)

    for c0 in range(24):
        cliff0 = Clifford(C1_TO_TABLEAU[c0], False)
        for c1 in range(24):
            cliff1 = Clifford(C1_TO_TABLEAU[c1], False)
            cliff_2q = cliff1.tensor(cliff0)
            result = gate_inv.dot(cliff_2q).dot(gate_cliff)
            tab = result.tableau

            # Check cross-qubit terms are zero (tensor product structure)
            if (
                tab[0, 1]
                or tab[0, 3]
                or tab[1, 0]
                or tab[1, 2]
                or tab[2, 1]
                or tab[2, 3]
                or tab[3, 0]
                or tab[3, 2]
            ):
                continue

            # Extract single-qubit tableaus
            tab0 = np.array(
                [[tab[0, 0], tab[0, 2], tab[0, 4]], [tab[2, 0], tab[2, 2], tab[2, 4]]],
                dtype=np.bool_,
            )
            tab1 = np.array(
                [[tab[1, 1], tab[1, 3], tab[1, 4]], [tab[3, 1], tab[3, 3], tab[3, 4]]],
                dtype=np.bool_,
            )

            idx0 = tableau_map.get(tab0.tobytes())
            idx1 = tableau_map.get(tab1.tobytes())
            if idx0 is not None and idx1 is not None:
                table[c0, c1] = [idx0, idx1]

    return table


C1_PAST_CLIFFORD_LOOKUP_TABLES = {
    "cx": _compute_2q_table("cx"),
    "cz": _compute_2q_table("cz"),
    "ecr": _compute_2q_table("ecr"),
}
"""Lookup tables for computing the conjugation of C1 operators by Clifford gates.

Single-qubit C1 operators are indexed as in :class:`~.C1Register`\\s. Computing the
conjugation of a C1 element by a Clifford can be done via slicing. For example,
``C1_PAST_CLIFFORD_LOOKUP_TABLES["cx"][i, j]`` gives that of C1 elements ``i`` and ``j`` by CX.
Two-qubit entries that do not remain local contain sentinel value ``-1``.
"""

C1_PAST_CLIFFORD_INVARIANTS = {"id"}
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
