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

"""UniformPauli"""

import numpy as np

from ..annotations import VirtualType
from ..virtual_registers import PauliRegister
from .distribution import Distribution


class BalancedUniformPauli(Distribution):
    r"""The balanced uniform distribution over virtual Pauli gates.

    Here, *balanced* means that on every qubit, each of the four Paulis appears the same number of
    times, provided that the requested number of samples is a multiple of four. The sampling
    algorithm is simply to draw four times fewer n-qubit Paulis uniformly and iid than requested,
    and then replicate each four times with respective multiplications by :math:`I^{\otimes}n`,
    :math:`X^{\otimes}n`, :math:`Y^{\otimes}n`, and :math:`Z^{\otimes}n`, truncating the samples
    if their requested number is not a multiple of four. Randomizations are ordered such that the
    four replications are consecutive.

    Args:
        num_subsystems: The number of subsystems this distribution samples.
    """

    @property
    def register_type(self):
        return VirtualType.PAULI

    def sample(self, size, rng):
        paulis = np.arange(4, dtype=PauliRegister.DTYPE).reshape(1, 1, 4) + rng.integers(
            0, 4, (self.num_subsystems, max(size // 4, 1), 1), dtype=PauliRegister.DTYPE
        )
        # the PauliRegister constructor with take care of the mod-4
        return PauliRegister(paulis.reshape(self.num_subsystems, -1)[:, :size])
