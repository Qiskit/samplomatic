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

"""UniformPauliSubset"""

import numpy as np

from ..virtual_registers import PauliRegister, VirtualType
from .distribution import Distribution


class UniformPauliSubset(Distribution):
    """The uniform distribution over a subset of virtual Pauli gates.

    Here, ``paulis`` is an array with elements corresponding to Paulis as enumerated in
    :class:`~.PauliRegister`. The length of an individual Pauli should be a divisor of
    ``num_subsystems``. The output :class:`~.PauliRegister` is partitioned
    contiguously such that each part samples independently from ``paulis``.

    .. plot::
        :include-source:
        :context:

        >>> import numpy as np
        >>> from samplomatic.distributions import UniformPauliSubset
        >>>
        >>> # Create a distribution that samples a random phase on each qubit
        >>> z_distribution = UniformPauliSubset(3, np.array([[0], [1]]))
        >>>
        >>> # Create a correlated phase distribution
        >>> z_corr_distribution = UniformPauliSubset(3, np.array([[0, 0, 0], [1, 1, 1]]))

    Args:
        num_subsystems: The number of subsystems this distribution samples.
        paulis: The subset of Paulis to sample from.

    Raises:
        ValueError: If the number of subsystems is not divisible by the length of an element of
            ``paulis``.
    """

    def __init__(self, num_subsystems: int, paulis: np.ndarray):
        super().__init__(num_subsystems)
        if num_subsystems % (subsys_size := paulis.shape[1]):
            raise ValueError(
                f"num_subsystem, '{num_subsystems}', must be divisible by subsystems "
                f"of the Paulis, '{subsys_size}'."
            )
        self._paulis = (paulis % 4).astype(PauliRegister.DTYPE)

    @property
    def register_type(self):
        return VirtualType.PAULI

    @property
    def paulis(self) -> np.ndarray:
        """The subset of Paulis to sample from."""
        return self._paulis

    def sample(self, size, rng):
        slices = rng.integers(
            0, len(self.paulis), self.num_subsystems // self.paulis.shape[1] * size
        )
        return PauliRegister(self.paulis[slices].reshape(self.num_subsystems, size))

    def __eq__(self, other):
        return (
            type(self) is type(other)
            and self.num_subsystems == other.num_subsystems
            and np.array_equal(self.paulis, other.paulis)
        )
