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

"""GroupMode"""

from enum import Enum
from typing import Literal

from ..aliases import TypeAlias


class GroupMode(str, Enum):
    """Which gate set and distribution to sample with."""

    PAULI = "pauli"
    """Sample the Pauli group uniformly and iid."""

    BALANCED = "balanced_pauli"
    """Sample the Pauli group, balancing the proportions of I, X, Y, and Z."""


GroupLiteral: TypeAlias = GroupMode | Literal["pauli", "balanced_pauli"]
"""Which gate set and distribution to sample with.

 * ``pauli``: Sample the Pauli group uniformly and iid.
 * ``balanced_pauli``: Sample the Pauli group, balancing the proportions of I, X, Y, and Z.
"""
