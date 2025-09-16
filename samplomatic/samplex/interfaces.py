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


"""Interfaces"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from ..tensor_interface import TensorInterface, TensorSpecification


class SamplexOutput(TensorInterface):
    """The output of a single call to :meth:`~Samplex.sample`.

    Args:
        specs: An iterable of specificaitons for the allowed data in this interface.
        metadata: Information relating to the process of sampling.
    """

    def __init__(
        self, specs: Iterable[TensorSpecification], metadata: dict[str, Any] | None = None
    ):
        super().__init__(specs)
        self._data = {spec.name: spec.empty() for spec in specs}
        self.metadata: dict[str, Any] = {} if metadata is None else metadata
