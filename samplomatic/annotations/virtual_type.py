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

"""VirtualType"""

from typing import Literal

from ..aliases import TypeAlias
from ..virtual_registers import VirtualType

TWIRLING_GROUPS = frozenset([VirtualType.PAULI])
"""Those :class:`VirtualType`\\s that represent unitary groups and have twirling support."""


GroupLiteral: TypeAlias = VirtualType | Literal["pauli"]
"""The type of group by which to twirl.

 * ``pauli``: The projective Pauli group.
"""
