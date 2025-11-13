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

"""C1Register"""

from __future__ import annotations

import numpy as np
from qiskit.quantum_info import Clifford

from ..aliases import SubsystemIndex
from ..annotations import VirtualType
from ..exceptions import VirtualGateError
from .group_register import GroupRegister


class C1Register(GroupRegister):
    r"""Virtual register of C1 gates.

    Here, we use the tableau representation of the form ``(x | z | phase)``. This is the symplectic
    matrix with the phases appended.
    """

    TYPE = VirtualType.C1
    GATE_SHAPE = (2, 3)
    SUBSYSTEM_SIZE = 1
    DTYPE = np.bool_
    CONVERTABLE_TYPES = frozenset({VirtualType.C1, VirtualType.U2})

    def __init__(self, virtual_gates):
        super().__init__(virtual_gates)

    @classmethod
    def identity(cls, num_subsystems, num_samples):
        arr = np.zeros((num_subsystems, num_samples) + cls.GATE_SHAPE, dtype=cls.DTYPE)
        arr[:, :, 0, 0] = arr[:, :, 1, 1] = 1
        return cls(arr)

    def convert_to(self, register_type):
        if register_type is VirtualType.U2:
            raise NotImplementedError(
                "Converting from `C1` to `U2` virtual registers is not yet supported."
            )
        return super().convert_to(register_type)

    def multiply(self, other, subsystem_idxs: list[SubsystemIndex] | slice = slice(None)):
        try:
            virtual_gates = self.virtual_gates[subsystem_idxs]
            shape = np.broadcast_shapes(virtual_gates.shape, other.virtual_gates.shape)
            array = np.empty(shape, dtype=self.DTYPE)

            reshape = (-1, *self.GATE_SHAPE)
            these_tableaus = np.broadcast_to(virtual_gates, shape).reshape(reshape)
            other_tableaus = np.broadcast_to(other.virtual_gates, shape).reshape(reshape)

            flat_array = array.reshape(-1, *self.GATE_SHAPE)
            for idx, (c1, c2) in enumerate(zip(these_tableaus, other_tableaus)):
                flat_array[idx, ...] = apply_clifford(c1, c2)
            return C1Register(array)
        except (ValueError, IndexError) as exc:
            raise VirtualGateError(
                f"Register {self} and {other} have incompatible shapes or types, "
                f"given subsystem_idxs {subsystem_idxs}"
            ) from exc

    def inplace_multiply(self, other, subsystem_idxs: list[SubsystemIndex] | slice = slice(None)):
        try:
            if isinstance(subsystem_idxs, slice):
                subsystem_idxs = list(range(*subsystem_idxs.indices(self.num_subsystems)))

            for other_idx, idx in enumerate(subsystem_idxs):
                for sample, (tableau, other_tableau) in enumerate(
                    zip(self.virtual_gates[idx], other.virtual_gates[other_idx])
                ):
                    self.virtual_gates[(idx, sample)] = apply_clifford(tableau, other_tableau)
        except (ValueError, IndexError) as exc:
            raise VirtualGateError(
                f"Register {self} and {other} have incompatible shapes or types, "
                f"given subsystem_idxs {subsystem_idxs}"
            ) from exc

    def left_multiply(self, other, subsystem_idxs: list[SubsystemIndex] | slice = slice(None)):
        try:
            virtual_gates = self.virtual_gates[subsystem_idxs]
            shape = np.broadcast_shapes(virtual_gates.shape, other.virtual_gates.shape)
            array = np.empty(shape, dtype=self.DTYPE)

            reshape = (-1, *self.GATE_SHAPE)
            these_tableaus = np.broadcast_to(virtual_gates, shape).reshape(reshape)
            other_tableaus = np.broadcast_to(other.virtual_gates, shape).reshape(reshape)

            flat_array = array.reshape(-1, *self.GATE_SHAPE)
            for idx, (c1, c2) in enumerate(zip(these_tableaus, other_tableaus)):
                flat_array[idx, ...] = apply_clifford(c2, c1)
            return C1Register(array)
        except (ValueError, IndexError) as exc:
            raise VirtualGateError(
                f"Register {self} and {other} have incompatible shapes or types, "
                f"given subsystem_idxs {subsystem_idxs}"
            ) from exc

    def left_inplace_multiply(
        self, other, subsystem_idxs: list[SubsystemIndex] | slice = slice(None)
    ):
        try:
            if isinstance(subsystem_idxs, slice):
                subsystem_idxs = list(range(*subsystem_idxs.indices(self.num_subsystems)))

            for other_idx, idx in enumerate(subsystem_idxs):
                for sample, (tableau, other_tableau) in enumerate(
                    zip(self.virtual_gates[idx], other.virtual_gates[other_idx])
                ):
                    self.virtual_gates[(idx, sample)] = apply_clifford(other_tableau, tableau)
        except (ValueError, IndexError) as exc:
            raise VirtualGateError(
                f"Register {self} and {other} have incompatible shapes or types, "
                f"given subsystem_idxs {subsystem_idxs}"
            ) from exc

    def invert(self):
        array = np.empty_like(self.virtual_gates)
        flat_array = array.reshape((-1, *self.GATE_SHAPE))
        reshaped_gates = self.virtual_gates.reshape((-1, *self.GATE_SHAPE))
        for idx in range(flat_array.shape[0]):
            flat_array[idx] = Clifford(reshaped_gates[idx]).adjoint().tableau
        return C1Register(array)

    def __setitem__(self, sl, value):
        super().__setitem__(sl, value)


# A lookup table for calculating phases. The indices are:
# current_x, current_z, running_x_count, running_z_count
_PHASE_LOOKUP = np.array([0, 0, 0, 0, 0, 0, -1, 1, 0, 1, 0, -1, 0, -1, 1, 0]).reshape(2, 2, 2, 2)


def apply_clifford(clifford_tableau, tableau):
    r"""Compute the action of an :math:`n`\-Clifford tableau on any other tableau.

    Both inputs should have the block-column structure ``x | z | phases`` of respective widths
    :math:`n`, :math`:`n`, and :math:`1`. When the second tableau happens to represent a Clifford,
    this method implements Clifford multiplication.

    Args:
        clifford_tableau: The Clifford to apply.
        tableau: The tableau to apply to.

    Returns:
        The action of the Clifford on the tableau.
    """
    num_qubits = clifford_tableau.shape[0] // 2

    # alias some slices
    c_x = clifford_tableau[:, :num_qubits].astype(np.uint8)
    c_z = clifford_tableau[:, num_qubits : 2 * num_qubits].astype(np.uint8)
    c_paulis = clifford_tableau[:, : 2 * num_qubits]
    c_phases = clifford_tableau[:, -1]

    s_paulis = tableau[:, : 2 * num_qubits]
    s_phases = tableau[:, -1]

    # Correcting for phase due to Pauli multiplication. Start with factors of -i from XZ = -iY
    # on individual qubits, and then handle multiplication between each qubitwise pair.
    i_factors = np.sum(s_paulis[:, :num_qubits] & s_paulis[:, num_qubits:], axis=1, dtype=int)

    for idx, s_pauli in enumerate(s_paulis):
        c_x_accum = np.logical_xor.accumulate(c_x_select := c_x[s_pauli], axis=0).astype(np.uint8)
        c_z_accum = np.logical_xor.accumulate(c_z_select := c_z[s_pauli], axis=0).astype(np.uint8)
        indexer = (c_x_select[1:], c_z_select[1:], c_x_accum[:-1], c_z_accum[:-1])
        i_factors[idx] += _PHASE_LOOKUP[indexer].sum()
    phases = np.mod(i_factors, 4) // 2

    # construct output tableau
    ret = np.empty((tableau.shape[0], 2 * num_qubits + 1), dtype=bool)
    ret[:, -1] = (np.matmul(s_paulis, c_phases, dtype=int) + s_phases + phases) % 2
    ret[:, :-1] = np.matmul(s_paulis, c_paulis, dtype=int) % 2

    return ret
