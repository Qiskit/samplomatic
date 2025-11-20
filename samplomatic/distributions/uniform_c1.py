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

"""UniformC1"""

from ..annotations import VirtualType
from ..virtual_registers import C1Register
from .distribution import Distribution


class UniformC1(Distribution):
    """The uniform distribution over virtual C1 gates.

    Args:
        num_subsystems: The number of subsystems this distribution samples.
    """

    @property
    def register_type(self):
        return VirtualType.C1

    def sample(self, size, rng):
        return C1Register(rng.integers(0, 24, (self.num_subsystems, size), dtype=C1Register.DTYPE))
