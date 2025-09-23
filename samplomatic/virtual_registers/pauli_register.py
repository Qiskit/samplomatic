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

"""PauliRegister"""

from __future__ import annotations

import numpy as np

from ..aliases import SubsystemIndex
from ..annotations import VirtualType
from ..exceptions import VirtualGateError
from .group_register import GroupRegister
from .u2_register import U2Register
from .z2_register import Z2Register

PAULI_TO_U2 = np.array(
    [np.diag([1, 1]), np.diag([1, -1]), np.diag([1, 1])[::-1], np.diag([-1j, 1j])[::-1]],
    dtype=U2Register.DTYPE,
)
"""An array storing a representation of the one-qubit Pauli gates as U2 matrices.

The matrix representations of the Paulis I, Z, X, and Y are in positions 0, 1, 2, and 3
respectively.
"""


class PauliRegister(GroupRegister):
    r"""Virtual register of virtual projective Pauli gates.

    Here, projective means we are modding out the centralizer, in other words, ignoring phases.

    The Paulis I, X, Y, and Z correspond to 0, 2, 3, and 1 respectively.
    The non-alphabetical assignment of Y and Z is because it is more convenient
    in most calculations to have them in symplectic ordering. I.e., for a projective
    Pauli operation :math:`P = X^x Z^z` with :math:`x,z\in\mathbb{Z}_2`, we
    order according to binary number `zx`.
    """

    TYPE = VirtualType.PAULI
    GATE_SHAPE = ()
    SUBSYSTEM_SIZE = 1
    DTYPE = np.uint8
    CONVERTABLE_TYPES = frozenset({VirtualType.Z2, VirtualType.U2, VirtualType.PAULI})

    def __init__(self, virtual_gates):
        super().__init__(virtual_gates)
        self._array %= 4

    @classmethod
    def identity(cls, num_subsystems, num_samples):
        return cls(np.zeros((num_subsystems, num_samples), dtype=np.uint8))

    def convert_to(self, register_type):
        if register_type is VirtualType.U2:
            return U2Register(PAULI_TO_U2[self._array, :, :])
        if register_type is VirtualType.Z2:
            # I, Z, X, and Y are 0, 1, 2, and 3 respectively
            return Z2Register(np.right_shift(self._array, 1))
        return super().convert_to(register_type)

    def multiply(self, other, subsystem_idxs: list[SubsystemIndex] | slice = slice(None)):
        try:
            return PauliRegister(
                np.bitwise_xor(self._array[subsystem_idxs, :], other.virtual_gates)
            )
        except (ValueError, IndexError) as exc:
            raise VirtualGateError(
                f"Register {self} and {other} have incompatible shapes or types, "
                f"given subsystem_idxs {subsystem_idxs}"
            ) from exc

    def inplace_multiply(self, other, subsystem_idxs: list[SubsystemIndex] | slice = slice(None)):
        try:
            self._array[subsystem_idxs, :] = np.bitwise_xor(
                self._array[subsystem_idxs, :], other.virtual_gates
            )
        except (ValueError, IndexError) as exc:
            raise VirtualGateError(
                f"Register {self} and {other} have incompatible shapes or types, "
                f"given subsystem_idxs {subsystem_idxs}"
            ) from exc

    def invert(self):
        return self.copy()

    def __setitem__(self, sl, value):
        super().__setitem__(sl, value)
        self._array %= 4
