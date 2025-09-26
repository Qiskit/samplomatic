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

"""Constants"""

from enum import IntEnum

__all__ = ["Direction", "SYMMETRIC_2Q_GATES"]


class Direction(IntEnum):
    """The direction that a virtual gate is traveling."""

    LEFT = 0
    RIGHT = 1
    BOTH = 2


SYMMETRIC_2Q_GATES: tuple[str] = (
    "cz",
    "swap",
    "rxx",
    "ryy",
    "rzz",
    "xx_minus_yy",
    "iswap",
    "cs",
    "csdg",
)
"""
The names of all the Qiskit built-in two-qubit gates that are invariant under qubit permutation.
"""
