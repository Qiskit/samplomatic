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

"""UniformLocalC1"""

import numpy as np

from ..samplex.nodes.c1_past_clifford_node import C1_PAST_CLIFFORD_LOOKUP_TABLES
from ..virtual_registers import C1Register, VirtualType
from .distribution import Distribution


class UniformLocalC1(Distribution):
    """The uniform distribution over C1⊗C1 elements that stay local under conjugation.

    For each pair of consecutive subsystems, independently draws a pair ``(c0, c1)``
    uniformly from the set of C1⊗C1 elements that remain factorized as C1⊗C1 after
    conjugation by the specified two-qubit gate.

    Args:
        num_subsystems: The number of subsystems this distribution samples. Must be even.
        gate: A two-qubit gate name whose conjugation table appears in
            :data:`~.C1_PAST_CLIFFORD_LOOKUP_TABLES`.
    """

    def __init__(self, num_subsystems: int, gate: str):
        super().__init__(num_subsystems)
        if num_subsystems % 2:
            raise ValueError(f"num_subsystems must be even, got {num_subsystems}.")

        if gate not in C1_PAST_CLIFFORD_LOOKUP_TABLES:
            raise ValueError(
                f"Unknown gate {gate!r}. Expected one of "
                f"{list(C1_PAST_CLIFFORD_LOOKUP_TABLES)}."
            )
        table = C1_PAST_CLIFFORD_LOOKUP_TABLES[gate]
        if table.ndim != 3:
            raise ValueError(f"Gate {gate!r} is not a two-qubit gate.")

        self._valid_pairs = np.argwhere(np.all(table >= 0, axis=-1)).astype(C1Register.DTYPE)
        self._gate = gate

    @property
    def register_type(self):
        return VirtualType.C1

    def sample(self, size, rng):
        num_pairs = self.num_subsystems // 2
        indices = rng.integers(0, len(self._valid_pairs), (num_pairs, size))
        pairs = self._valid_pairs[indices]

        data = np.empty((self.num_subsystems, size), dtype=C1Register.DTYPE)
        data[0::2] = pairs[:, :, 0]
        data[1::2] = pairs[:, :, 1]

        return C1Register(data)

    def __eq__(self, other):
        return (
            type(self) is type(other)
            and self.num_subsystems == other.num_subsystems
            and self._gate == other._gate
        )
