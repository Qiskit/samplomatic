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

from ..aliases import SubsystemIndex
from ..annotations import VirtualType
from .group_register import GroupRegister


class C1Register(GroupRegister):
    r"""Virtual register of C1 gates.

    Here, we use the tableau representation of the form ``(x | z | phase)``. This is the symplectic
    matrix with the phases appended.
    """

    TYPE = VirtualType.C1
    GATE_SHAPE = (2, 3)
    SUBSYSTEM_SIZE = 1
    DTYPE = np.uint8
    CONVERTABLE_TYPES = frozenset({VirtualType.C1, VirtualType.U2})

    def __init__(self, virtual_gates):
        super().__init__(virtual_gates)
        self._array %= 2

    @classmethod
    def identity(cls, num_subsystems, num_samples):
        return cls(np.zeros((num_subsystems, num_samples, *cls.GATE_SHAPE), dtype=np.uint8))

    def convert_to(self, register_type):
        if register_type is VirtualType.U2:
            raise NotImplementedError()
        return super().convert_to(register_type)

    def multiply(self, other, subsystem_idxs: list[SubsystemIndex] | slice = slice(None)):
        raise NotImplementedError()

    def inplace_multiply(self, other, subsystem_idxs: list[SubsystemIndex] | slice = slice(None)):
        raise NotImplementedError()

    def invert(self):
        raise NotImplementedError()

    def __setitem__(self, sl, value):
        super().__setitem__(sl, value)
        self._array %= 2
