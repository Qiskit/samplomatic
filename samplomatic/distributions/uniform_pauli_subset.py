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

from functools import partial

import numpy as np

from ..virtual_registers import PauliRegister, VirtualType
from .distribution import Distribution

LOOKUP_TABLES = {
    "rzz": np.array([[0, 0], [0, 1], [1, 0], [1, 1], [2, 2], [2, 3], [3, 2], [3, 3]]),
    "phase": np.array([[0], [1]]),
}
"""Lookup tables for common distributions."""


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

    @classmethod
    def from_name(cls, num_subsystems: int, name: str) -> "UniformPauliSubset":
        """Return a new instance from a specific distribution name.

        Args:
            num_subsystems: The number of subsystems this distribution samples.
            name: The distribution name to use.

        Returns:
            The new distribution.
        """
        return cls(num_subsystems, LOOKUP_TABLES[name])

    @property
    def register_type(self):
        return VirtualType.PAULI

    @property
    def paulis(self) -> np.ndarray:
        """The subset of Paulis to sample from."""
        return self._paulis

    def sample(self, size, rng):
        pauli_width = self.paulis.shape[1]
        num_groups = self.num_subsystems // pauli_width
        slices = rng.integers(0, len(self.paulis), num_groups * size)
        raw = self.paulis[slices].reshape(num_groups, size, pauli_width)
        return PauliRegister(raw.transpose(0, 2, 1).reshape(self.num_subsystems, size))

    def __eq__(self, other):
        return (
            type(self) is type(other)
            and self.num_subsystems == other.num_subsystems
            and np.array_equal(self.paulis, other.paulis)
        )


uniform_phase = partial(UniformPauliSubset.from_name, name="phase")
