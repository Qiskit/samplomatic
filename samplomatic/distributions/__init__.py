# This code is a Qiskit project.
#
# (C) Copyright IBM 2025-2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Distributions"""

from ..annotations import GroupMode as _GroupMode
from ..utils import FrozenDict as _FrozenDict
from .balanced_uniform_pauli import BalancedUniformPauli
from .distribution import Distribution
from .haar_u2 import HaarU2
from .uniform_c1 import UniformC1
from .uniform_local_c1 import UniformLocalC1
from .uniform_pauli import UniformPauli
from .uniform_pauli_subset import UniformPauliSubset

GROUP_TO_DISTRIBUTION: dict[_GroupMode, type[Distribution]] = _FrozenDict(
    {
        _GroupMode.PAULI: UniformPauli,
        _GroupMode.BALANCED: BalancedUniformPauli,
        _GroupMode.LOCAL_C1: UniformLocalC1,
    }
)
