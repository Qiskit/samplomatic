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

import numpy as np

from ..annotations import VirtualType
from .finite_group_register import FiniteGroupRegister
from .tables.c1_tables import C1_INVERSE_TABLE, C1_LOOKUP_TABLE

C1_TO_TABLEAU = np.array(
    [
        [[True, False, False], [False, True, False]],
        [[True, False, True], [False, True, False]],
        [[True, False, False], [False, True, True]],
        [[True, False, True], [False, True, True]],
        [[False, True, False], [True, False, False]],
        [[False, True, True], [True, False, False]],
        [[False, True, False], [True, False, True]],
        [[False, True, True], [True, False, True]],
        [[True, True, True], [True, False, False]],
        [[True, True, False], [True, False, False]],
        [[True, True, True], [True, False, True]],
        [[True, True, False], [True, False, True]],
        [[True, False, False], [True, True, True]],
        [[True, False, True], [True, True, True]],
        [[True, False, False], [True, True, False]],
        [[True, False, True], [True, True, False]],
        [[False, True, False], [True, True, True]],
        [[False, True, True], [True, True, True]],
        [[False, True, False], [True, True, False]],
        [[False, True, True], [True, True, False]],
        [[True, True, True], [False, True, False]],
        [[True, True, False], [False, True, False]],
        [[True, True, True], [False, True, True]],
        [[True, True, False], [False, True, True]],
    ],
    np.bool_,
)
"""An array containing the tableaus of each single-qubit Clifford.

This is the order used by :class:`~.C1Register`."""


class C1Register(FiniteGroupRegister):
    """Virtual register of C1 gates.

    Here, we use an integer representation constructed from flattening the six cosets of the
    Pauli subgroup and the subgroup itself. Concretely, a value :math:`c` corresponds to the unitary
    :math:`G^i H^j P(k)` where :math:`k = c % 4, j = c // 4 % 2, i = c // 8 % 3` and :math:`G = HS`.
    """

    TYPE = VirtualType.C1
    GATE_SHAPE = ()
    SUBSYSTEM_SIZE = 1
    DTYPE = np.uint8
    CONVERTABLE_TYPES = frozenset({VirtualType.C1, VirtualType.U2})

    @property
    def inverse_table(self) -> np.ndarray:
        return C1_INVERSE_TABLE

    @property
    def lookup_table(self) -> np.ndarray:
        return C1_LOOKUP_TABLE

    def convert_to(self, register_type):
        if register_type is VirtualType.U2:
            NotImplementedError("Not yet implemented.")
        return super().convert_to(register_type)

    @classmethod
    def identity(cls, num_subsystems, num_samples):
        return cls(np.zeros((num_subsystems, num_samples), dtype=np.uint8))

    @classmethod
    def from_tableau(cls, tableaus: np.typing.ArrayLike) -> "C1Register":
        """Return a new register from an array of tableaus.

        Args:
            tableaus: The tableaus corresponding the registers.

        Returns:
            A virtual register in the enumerated representation.
        """
        raise NotImplementedError("Not yet implemented.")

    def to_tableau(self) -> np.ndarray:
        """Return an array of tableaus with the same shape as this.

        Returns:
            An array of tableaus.
        """
        return C1_TO_TABLEAU[self.virtual_gates]
