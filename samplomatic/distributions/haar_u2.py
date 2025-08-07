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

"""HaarU2"""

import numpy as np

from ..annotations import VirtualType
from ..virtual_registers import U2Register
from .distribution import Distribution


class HaarU2(Distribution):
    """The Haar distribution over 2x2 unitary virtual gates.

    Args:
        num_subsystems: The number of subsystems this distribution samples.
    """

    @property
    def register_type(self):
        return VirtualType.U2

    def sample(self, size, rng):
        shape = (self.num_subsystems, size, 2, 2)

        # draw from ginibre ensemble
        ginibre = np.empty(shape, dtype=U2Register.DTYPE)
        ginibre.real = rng.standard_normal(shape)
        ginibre.imag = rng.standard_normal(shape)

        # take QR decomp of each one
        u2, r = np.linalg.qr(ginibre)

        # normalize columns by complex moduli of R diags to unbunch eigenvals
        u2[..., :, 0] *= r[..., :1, 0]
        u2[..., :, 0] /= np.abs(r[..., :1, 0])
        u2[..., :, 1] *= r[..., 1:, 1]
        u2[..., :, 1] /= np.abs(r[..., 1:, 1])

        return U2Register(u2)
