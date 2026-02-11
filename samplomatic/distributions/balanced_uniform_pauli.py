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

"""BalancedUniformPauli"""

import numpy as np

from ..virtual_registers import PauliRegister, VirtualType
from .distribution import Distribution

_MULTIPLIERS = np.array([0, 2, 1, 3], dtype=PauliRegister.DTYPE).reshape(1, 1, 4)


class BalancedUniformPauli(Distribution):
    """The balanced uniform distribution over virtual Pauli gates.

    Here, *balanced* means that on every qubit, each of the four Paulis appears the same number of
    times, provided that the requested number of samples is a multiple of four. Moreover, when the
    number of samples is a multiple of two, it is promised that, for each qubit, X or Y is
    sampled the same number of times as I or Z.

    The sampling algorithm is simply to draw four times fewer n-qubit Paulis uniformly and iid than
    requested, and then replicate each four times with respective multiplications by
    :math:`I^{\otimes}n`, :math:`X^{\otimes}n`, :math:`Z^{\otimes}n`, and :math:`Y^{\otimes}n`,
    truncating the samples if their requested number is not a multiple of four. Randomizations are
    ordered such that the four replications are consecutive. The particular ordering of the
    four multiplicitive terms--- :math:`I` then :math:`X` then :math:`Z` then :math:`Y` ---is what
    provides the guarantee that for each qubit, X or Y is sampled the same number of times as I or
    Z, even if the number of samples is even but not a multiple of four.

    Args:
        num_subsystems: The number of subsystems this distribution samples.
    """

    @property
    def register_type(self):
        return VirtualType.PAULI

    def sample(self, size, rng):
        paulis = _MULTIPLIERS + rng.integers(
            0, 4, (self.num_subsystems, size // 4 + bool(size % 4), 1), dtype=PauliRegister.DTYPE
        )
        # the PauliRegister constructor with take care of the mod-4
        return PauliRegister(paulis.reshape(self.num_subsystems, -1)[:, :size])
