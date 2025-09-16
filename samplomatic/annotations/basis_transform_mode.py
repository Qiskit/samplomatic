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

"""BasisTransformMode"""

from __future__ import annotations

from enum import Enum
from typing import Literal, Union

from ..aliases import TypeAlias


class BasisTransformMode(str, Enum):
    """Whether to add basis transform gates to prepare or measure a given basis."""

    MEASURE = "measure"
    PREPARE = "prepare"


BasisTransformLiteral: TypeAlias = Union[BasisTransformMode, Literal["measure", "prepare"]]
"""Allowed basis transform modes.

 * ``measure``: Gate collection templates are placed on the left side of boxes. The adjoint of the
    basis changing gate is absorbed into the template.
 * ``prepare``: Gate collection templates are placed on the right side of boxes. The basis changing
    gate is absorbed into the template.
"""
