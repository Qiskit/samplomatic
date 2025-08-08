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

"""SamplexOutput"""

import abc
from collections.abc import Iterable, Mapping
from typing import Generic, TypeVar

import numpy as np

from ..aliases import OutputName

OutputT = TypeVar("OutputT")


class OutputSpecification(abc.ABC, Generic[OutputT]):
    """Specification of a single named output from a samplex.

    Args:
        name: The name of the output.
        description: A description of what the output represents.
    """

    def __init__(self, name: OutputName, description: str = ""):
        self.name: OutputName = name
        self.description: str = description

    def __repr__(self):
        return f"{type(self).__name__}({repr(self.name)}, {repr(self.description)})"

    @abc.abstractmethod
    def create_empty(self, num_samples: int) -> OutputT:
        """Create an empty output according to this specification.

        Args:
            num_samples: How many samples have been requested.

        Returns:
            An empty output according to this specification.
        """


class ArrayOutput(OutputSpecification[np.ndarray]):
    """Specification of a single output array from a samplex.

    Args:
        name: The name of the output.
        shape: The trailing shape of the array past the samples axis.
        dtype: The data type of the array.
        description: A description of what the output represents.
    """

    def __init__(
        self, name: OutputName, shape: tuple[int, ...], dtype: type, description: str = ""
    ):
        super().__init__(name, description=description)
        self.dtype: type = dtype
        self.shape: tuple[int, ...] = shape

    def __repr__(self):
        return (
            f"{type(self).__name__}({repr(self.name)}, {self.shape}, "
            f"{self.dtype}, {repr(self.description)})"
        )

    def create_empty(self, num_samples: int) -> np.ndarray:
        return np.empty((num_samples,) + self.shape, dtype=self.dtype)


class Z2ArrayOutput(ArrayOutput):
    """Specification of a zero-initialized z2 output array from a samplex.

    Args:
        name: The name of the output.
        shape: The trailing shape of the array past the samples axis.
        description: A description of what the output represents.
    """

    def __init__(self, name: OutputName, shape: tuple[int, ...], description: str = ""):
        super().__init__(name, shape, np.bool_, description=description)

    def create_empty(self, num_samples: int) -> np.ndarray:
        return np.zeros((num_samples,) + self.shape, dtype=self.dtype)


class MetadataOutput(OutputSpecification[dict]):
    """Specification of a free-form dict output.

    Args:
        name: The name of the output.
        description: A description of what the output represents.
    """

    def create_empty(self, num_samples: int) -> dict:
        return {}


class SamplexOutput(Mapping):
    """The output of a single call to :meth:`~Samplex.sample`.

    Args:
        specifiers: A specification of what is present in the output.
        num_samples: How many samples are drawn.
    """

    def __init__(self, specifiers: Iterable[OutputSpecification], num_samples: int):
        self.specifiers = sorted(specifiers, key=lambda specifier: specifier.name)
        self.num_samples = num_samples

        self._data = {
            specifier.name: specifier.create_empty(num_samples) for specifier in self.specifiers
        }

    def __repr__(self):
        return f"{type(self).__name__}({repr(self.specifiers)}, {self.num_samples})"

    def __str__(self):
        lines = [f"{type(self).__name__}(\n  ["]
        lines.extend(f"    {specifier}," for specifier in self.specifiers)
        lines.append(f"  ],\n  num_samples={self.num_samples},\n)")
        return "\n".join(lines)

    def __contains__(self, key):
        return key in self._data

    def __getitem__(self, key):
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)
