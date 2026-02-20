# This code is a Qiskit project.
#
# (C) Copyright IBM 2025, 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""VirtualType"""

from typing import Literal

from ..aliases import TypeAlias
from ..virtual_registers import VirtualType

TWIRLING_GROUPS = frozenset([VirtualType.PAULI, VirtualType.LOCAL_C1])
"""Those :class:`VirtualType`\\s that represent unitary groups and have twirling support."""

GATE_DEPENDENT_TWIRLING_GROUPS = frozenset([VirtualType.LOCAL_C1])
"""A subset of twirling groups that depend on the entangler."""


GroupLiteral: TypeAlias = VirtualType | Literal["pauli", "local_c1"]
"""The type of group by which to twirl.

 * ``pauli``: The projective Pauli group.
 * ``local_c1``: The subset of C1 gates that remain local under the action of an entangler, or the
        project Pauli group if no entangler is present.
"""
