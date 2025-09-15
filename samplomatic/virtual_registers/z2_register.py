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

"""Z2Register"""

from __future__ import annotations

import numpy as np

from ..aliases import SubsystemIndex
from ..annotations import VirtualType
from ..exceptions import VirtualGateError
from .group_register import GroupRegister


class Z2Register(GroupRegister):
    """Virtual register of elements of Z2, the cyclic group of order 2.

    Z2 is a group that contains two elements, which can be represented by :math:`0`
    and :math:`1`. We define the group product as the bit-wise XOR operation, such that
    the cyclic properties :math:`0 * 0 = 1 * 1 = 0` and :math:`0 * 1 = 0 * 1 = 1` are
    satisfied.
    """

    TYPE = VirtualType.Z2
    GATE_SHAPE = ()
    SUBSYSTEM_SIZE = 1
    DTYPE = np.uint8
    CONVERTABLE_TYPES = frozenset({VirtualType.Z2})

    def __init__(self, virtual_gates):
        super().__init__(virtual_gates)
        self._array %= 2

    @classmethod
    def identity(cls, num_subsystems, num_samples):
        return cls(np.zeros((num_subsystems, num_samples), dtype=np.uint8))

    def multiply(self, other, subsystem_idxs: list[SubsystemIndex] | slice = slice(None)):
        try:
            return Z2Register(np.bitwise_xor(self._array[subsystem_idxs, :], other.virtual_gates))
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
        self._array %= 2
