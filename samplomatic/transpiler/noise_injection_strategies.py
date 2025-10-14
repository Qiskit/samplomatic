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

"""NoiseInjectionStrategy"""

from __future__ import annotations

from enum import Enum
from typing import Literal, Union

from ..aliases import TypeAlias


class NoiseInjectionStrategy(str, Enum):
    """The noise inejection strategies supported by the boxing pass manager."""

    NO_MODIFICATION = "no_modification"
    UNIFORM_MODIFICATION = "uniform_modification"
    INDIVIDUAL_MODIFICATION = "individual_modification"


NoiseInjectionStrategyLiteral: TypeAlias = Union[
    NoiseInjectionStrategy,
    Literal["no_modification", "uniform_modification", "individual_modification"],
]
"""The noise injection strategies supported by the :class:`~AddInjectNoise` pass.

The following options are supported. In all these options, by "equivalent boxes" we mean boxes that
are equal up to single-qubit qubit gates on the dressing side.

 * ``'no_modification'``: All the equivalent boxes are assigned an inject noise annotation with the
    same ``ref`` and with ``modifier_ref=''``.
 * ``'uniform_modification'``: All the equivalent boxes are assigned an inject noise annotation
    with the same ``ref`` and with ``modifier_ref=ref``.
 * ``'individual_modification'``: All the equivalent boxes are assigned an inject noise annotation
    with the same ``ref``. Every box is assigned a unique ``modifier_ref``.
"""
