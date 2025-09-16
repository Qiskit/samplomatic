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

"""U2Register"""

from __future__ import annotations

import numpy as np

from ..aliases import SubsystemIndex
from ..annotations import VirtualType
from ..exceptions import VirtualGateError
from .group_register import GroupRegister

EPS12: float = 1e-12


class U2Register(GroupRegister):
    """Virtual register of 2x2 Unitary matrices.

    The equality method of this class is overridden to ignore global phase.
    """

    TYPE = VirtualType.U2
    GATE_SHAPE = (2, 2)
    SUBSYSTEM_SIZE = 1
    DTYPE = np.complex128
    CONVERTABLE_TYPES = frozenset({VirtualType.U2})

    @classmethod
    def identity(cls, num_subsystems, num_samples):
        arr = np.zeros((num_subsystems, num_samples) + cls.GATE_SHAPE, dtype=cls.DTYPE)
        arr[:, :, 0, 0] = arr[:, :, 1, 1] = 1
        return cls(arr)

    def multiply(self, other, subsystem_idxs: list[SubsystemIndex] | slice = slice(None)):
        try:
            return U2Register(
                np.einsum(
                    "abcx,abxd->abcd",
                    self._array[subsystem_idxs],
                    other.virtual_gates,
                    optimize=True,
                )
            )
        except (ValueError, IndexError) as exc:
            raise VirtualGateError(
                f"Register {self} and {other} have incompatible shapes or types, "
                f"given subsystem_idxs {subsystem_idxs}"
            ) from exc

    def inplace_multiply(self, other, subsystem_idxs: list[SubsystemIndex] | slice = slice(None)):
        try:
            self._array[subsystem_idxs] = np.einsum(
                "abcx,abxd->abcd",
                self._array[subsystem_idxs],
                other.virtual_gates,
                optimize=True,
            )
        except (ValueError, IndexError) as exc:
            raise VirtualGateError(
                f"Register {self} and {other} have incompatible shapes or types, "
                f"given subsystem_idxs {subsystem_idxs}"
            ) from exc

    def left_multiply(self, other, subsystem_idxs: list[SubsystemIndex] | slice = slice(None)):
        try:
            return U2Register(
                np.einsum(
                    "abcx,abxd->abcd",
                    other.virtual_gates,
                    self._array[subsystem_idxs],
                    optimize=True,
                )
            )
        except (ValueError, IndexError) as exc:
            raise VirtualGateError(
                f"Register {self} and {other} have incompatible shapes or types, "
                f"given subsystem_idxs {subsystem_idxs}"
            ) from exc

    def left_inplace_multiply(
        self, other, subsystem_idxs: list[SubsystemIndex] | slice = slice(None)
    ):
        try:
            self._array[subsystem_idxs, :, :, :] = np.einsum(
                "abcx,abxd->abcd",
                other.virtual_gates,
                self._array[subsystem_idxs],
                optimize=True,
            )
        except (ValueError, IndexError) as exc:
            raise VirtualGateError(
                f"Register {self} and {other} have incompatible shapes or types, "
                f"given subsystem_idxs {subsystem_idxs}"
            ) from exc

    def invert(self):
        return U2Register(self._array.conj().transpose(0, 1, 3, 2))

    def __eq__(self, other):
        if isinstance(other, U2Register) and self.shape == other.shape:
            shape = self.shape + (-1,)
            prefidelities = np.sum(
                self._array.reshape(shape) * other.virtual_gates.reshape(shape).conj(), axis=-1
            )
            return np.all(np.abs(np.real(prefidelities * prefidelities.conj()) / 4 - 1) < EPS12)
        return False
