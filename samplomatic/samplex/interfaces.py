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


"""SamplexInterface"""

from collections.abc import Iterable, Mapping
from typing import Any

import numpy as np

from ..aliases import InterfaceName
from ..exceptions import SamplexInputError


class MetadataOutput:
    """Specification of a free-form dict output.

    Args:
        name: The name of the output.
        description: A description of what the output represents.
    """

    def __init__(self, name: InterfaceName, description: str = ""):
        self.name: InterfaceName = name
        self.description: str = description

    def _to_json_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "description": self.description,
        }

    @classmethod
    def _from_json(cls, data: dict[str, Any]) -> "MetadataOutput":
        return cls(**data)


class TensorSpecification:
    """Specification of a single named tensor interface.

    Args:
        name: The name of the interface.
        shape: The shape of the input array.
        dtype: The data type of the array.
        description: A description of what the interface represents.
    """

    def __init__(
        self, name: InterfaceName, shape: tuple[int, ...], dtype: type, description: str = ""
    ):
        self.name: InterfaceName = name
        self.shape = shape
        self.dtype = dtype
        self.description: str = description

    def _to_json_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "dtype": self.dtype.__name__,
            "shape": tuple(int(x) for x in self.shape),
        }

    @classmethod
    def _from_json(cls, data: dict[str, Any]) -> "TensorSpecification":
        return cls(
            data["name"], tuple(data["shape"]), getattr(np, data["dtype"]), data["description"]
        )

    def empty(self, num_samples: int) -> np.ndarray:
        """Create an empty output according to this specification.

        Args:
            num_samples: How many samples have been requested.

        Returns:
            An empty output according to this specification.
        """
        return np.empty((num_samples,) + self.shape, dtype=self.dtype)

    def validate(self, array: np.ndarray):
        """Validate an array input against the specification.

        Args:
            array: The input to validate.

        Raises:
            SamplexInputError: If the input is not valid.
        """
        if array.dtype != self.dtype or array.shape != self.shape:
            raise SamplexInputError(
                f"Input ``{self.name}`` expects an array of shape `{self.shape}` and type "
                f"`{self.dtype}` but received {array}."
            )

    def __repr__(self):
        return f"{type(self).__name__}({repr(self.name)}, {repr(self.description)})"


class TensorInterface(Mapping):
    """An interface with tensor specifications.

    Args:
        specifiers: Specifications of the interface.
        num_samples: The number of samples.
    """

    def __init__(self, specifiers: Iterable[TensorSpecification], num_samples: int):
        self.num_samples: int = num_samples
        self.specifiers: list[TensorSpecification] = sorted(
            specifiers, key=lambda specifier: specifier.name
        )
        self._data: dict[InterfaceName, np.ndarray] = {}

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


class SamplexInput(TensorInterface):
    """The input of a single call to :meth:`~Samplex.sample`.

    Args:
        specifiers: A specification of what is present in the input.
        num_samples: The number of samples.
    """

    def __init__(
        self,
        specifiers: Iterable[TensorSpecification],
        num_samples: int,
    ):
        super().__init__(specifiers, num_samples)
        self._data.update({specifier.name: None for specifier in self.specifiers})

    def validate_and_update(self, **inputs: dict[InterfaceName, np.ndarray]):
        """Validate and update input data.

        Args:
            inputs: The inputs to validate.

        Raises:
            SamplexInputError: If any of the input interfaces are missing from ``inputs``.
        """
        for specifier in self.specifiers:
            if (input := inputs.get(interface := specifier.name)) is None:
                raise SamplexInputError(f"Samplex requires an input named {interface}.")
            specifier.validate(input)
            self._data[interface] = input


class SamplexOutput(TensorInterface):
    """The output of a single call to :meth:`~Samplex.sample`.

    Args:
        specifiers: A specification of what tensor interfaces are present in the output.
        metadata: Metadata present in this output.
        num_samples: The number of samples.
    """

    def __init__(
        self,
        specifiers: Iterable[TensorSpecification],
        metadata: Iterable[MetadataOutput],
        num_samples: int,
    ):
        super().__init__(specifiers, num_samples)
        self._data.update(
            {specifier.name: specifier.empty(self.num_samples) for specifier in self.specifiers}
        )
        self.metadata = {metadata_spec.name: {} for metadata_spec in metadata}
