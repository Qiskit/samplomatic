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


"""SamplexInput"""

import abc
from collections.abc import Iterable
from typing import Any, TypeVar

import numpy as np

from ...aliases import InterfaceName
from ...exceptions import SamplexInputError
from .samplex_interface import InterfaceSpecification, SamplexInterface

InputT = TypeVar("InputT")


class InputSpecification(InterfaceSpecification[InputT]):
    """Specification of a single named samplex input.

    Args:
        name: The name of the input.
        description: A description of what the intput represents.
    """

    @abc.abstractmethod
    def validate(self, input: InputT):
        """Validate an input.

        Args:
            input: The input to validate.

        Raises:
            SamplexInputError: If the input is not valid.
        """


class ArrayInput(InputSpecification[np.ndarray]):
    """Specification of a single input array for a samplex.

    Args:
        name: The name of the input.
        shape: The shape of the input array.
        dtype: The data type of the array.
        description: A description of what the output represents.
        optional: Whether the input is optional.
    """

    def __init__(
        self,
        name: InterfaceName,
        shape: tuple[int, ...],
        dtype: type,
        description: str = "",
    ):
        super().__init__(name, description=description)
        self.dtype: type = dtype
        self.shape: tuple[int, ...] = shape

    def __repr__(self):
        return (
            f"{type(self).__name__}({repr(self.name)}, {self.shape}, "
            f"{self.dtype}, {repr(self.description)})"
        )

    def validate(self, input: Any):
        # TODO: consider loosening type and shape to castable and broadcastable
        if (
            not isinstance(input, np.ndarray)
            or input.dtype != self.dtype
            or input.shape != self.shape
        ):
            raise SamplexInputError(
                f"Input ``{self.name}`` expects an array of shape `{self.shape}` and type "
                f"`{self.dtype}` but received {input}."
            )


class SamplexInput(SamplexInterface):
    """The input of a single call to :meth:`~Samplex.sample`.

    Args:
        specifiers: A specification of what is present in the input.
    """

    def __init__(self, specifiers: Iterable[InputSpecification]):
        self.specifiers = sorted(specifiers, key=lambda specifier: specifier.name)
        self._data = {specifier.name: None for specifier in specifiers}

    @property
    def inputs(self) -> list[InterfaceName]:
        """The inputs."""
        return list(self)

    def validate_and_update(self, **inputs: dict[InterfaceName, Any]):
        """Validate and update the input data.

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

    def __repr__(self):
        return f"{type(self).__name__}({repr(self.specifiers)})"

    def __str__(self):
        lines = [f"{type(self).__name__}(\n  ["]
        lines.extend(f"    {specifier}," for specifier in self.specifiers)
        lines.append("  ],\n)")
        return "\n".join(lines)

    def __setitem__(self, key, value):
        self._data[key] = value
