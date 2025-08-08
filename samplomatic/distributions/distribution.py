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

"""Distribution"""

import abc

from numpy.random import Generator

from ..annotations import VirtualType
from ..virtual_registers import VirtualRegister


class Distribution(abc.ABC):
    """A distribution over virtual gates.

    Args:
        num_subsystems: The number of subsystems that this distribution samples.
    """

    def __init__(self, num_subsystems: int):
        self.num_subsystems = num_subsystems

    @property
    @abc.abstractmethod
    def register_type(self) -> VirtualType:
        """The virtual gate type being sampled."""

    @abc.abstractmethod
    def sample(self, size: int, rng: Generator) -> VirtualRegister:
        """Sample the distribution.

        Args:
            size: The number elements to sample.
            rng: A randomness generator.

        Returns:
            The samples.
        """

    def __repr__(self):
        return (
            f"{type(self).__name__}(<num_subsystems={self.num_subsystems}, "
            f"register_type={self.register_type}>)"
        )
