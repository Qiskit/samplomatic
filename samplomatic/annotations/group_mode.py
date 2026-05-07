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
    """Which set of gates and distribution to sample with."""

    PAULI = "pauli"
    """Sample the Pauli group uniformly and iid."""

    BALANCED = "balanced_pauli"
    """Sample the Pauli group, balancing the proportions of I, X, Y, and Z."""

    LOCAL_C1 = "local_c1"
    """Sample C1 gates that stay C1 under conjugation by an entangler uniformly and iid.

    Sample the Pauli group if no entangler is present.
    """

    PARAMETRIC_RZZ = "parametric_rzz"
    """Sample from the commutant of RZZ uniformly and iid.

    The commutant consists of the 8 two-qubit Paulis that commute with ZZ for any angle.
    Sample the Pauli group if no RZZ is present.
    """

    PHASE = "phase"
    """Sample the phase group I, Z uniformly and iid."""


GATE_DEPENDENT_TWIRLING_GROUPS = frozenset([GroupMode.LOCAL_C1, GroupMode.PARAMETRIC_RZZ])
"""A subset of group modes that depend on an entangler."""


GroupLiteral: TypeAlias = (
    GroupMode | Literal["pauli", "balanced_pauli", "local_c1", "parametric_rzz", "phase"]
)
"""Which set of gates and distribution to sample with.

 * ``pauli``: Sample the Pauli group uniformly and iid.
 * ``balanced_pauli``: Sample the Pauli group, balancing the proportions of I, X, Y, and Z.
 * ``local_c1``: Sample C1 gates that stay C1 under conjugation by an entangler uniformly and iid.
 * ``parametric_rzz``: Sample from the commutant of RZZ uniformly and iid.
 * ``phase``: Sample the phase group I, Z uniformly and iid.
"""
