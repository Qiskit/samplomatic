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

"""QuantumProgramResult."""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import TYPE_CHECKING, Any, overload

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

    import numpy as np

    from .datatree import DataTree


class QuantumProgramItemResult(MutableMapping):
    """A container to store results for a single item of a :class:`QuantumProgram`.

    Args:
        result: A dictionary with array-valued data.
        metadata: The metadata produced for the individual item.
    """

    def __init__(
        self,
        result: dict[str, np.ndarray],
        metadata: Any = None,
    ):
        self._result = result
        self.metadata = metadata

    def __getitem__(self, key: str) -> np.ndarray:
        return self._result[key]

    def __setitem__(self, key: str, value: np.array) -> None:
        self._result[key] = value

    def __delitem__(self, key: str) -> None:
        del self._result[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._result)

    def __len__(self) -> int:
        return len(self._result)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._result}, metadata={self.metadata})"


class QuantumProgramResult:
    """A container to store results from executing a :class:`QuantumProgram`.

    Args:
        data: A list of dictionaries with array-valued data.
        metadata: A dictionary of metadata.
        passthrough_data: Arbitrary nested data passed through execution without modification.
    """

    def __init__(
        self,
        data: Sequence[dict[str, np.ndarray] | QuantumProgramItemResult],
        metadata: Any = None,
        passthrough_data: DataTree | None = None,
    ):
        self._data = [
            datum
            if isinstance(datum, QuantumProgramItemResult)
            else QuantumProgramItemResult(datum)
            for datum in data
        ]
        self.metadata = metadata
        self.passthrough_data = passthrough_data

    def __iter__(self) -> Iterator[QuantumProgramItemResult]:
        yield from self._data

    @overload
    def __getitem__(self, idx: int) -> QuantumProgramItemResult: ...

    @overload
    def __getitem__(self, idx: slice) -> list[QuantumProgramItemResult]: ...

    def __getitem__(
        self, idx: int | slice
    ) -> QuantumProgramItemResult | list[QuantumProgramItemResult]:
        return self._data[idx]

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(<{len(self)} results>)"
