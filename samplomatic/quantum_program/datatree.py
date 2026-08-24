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

"""DataTree."""

from typing import TypeAlias

import numpy as np

DataTree: TypeAlias = (
    list["DataTree"] | dict[str, "DataTree"] | np.ndarray[float] | str | float | int | bool | None
)
"""Arbitrary nesting of lists and dicts with typed leaves."""
