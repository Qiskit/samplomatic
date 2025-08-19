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
from enum import StrEnum
from typing import Any, Literal, Self, overload

import numpy as np
from qiskit.quantum_info import PauliLindbladMap

from ..aliases import InterfaceName
from ..exceptions import SamplexInputError


class ValueType(StrEnum):
    BOOL = "bool"
    INT = "int"
    LINDBLAD = "lindblad"
    NUMPY_ARRAY = "numpy_array"


class Specification:
    """A specification.

    Args:
        name: The name of the specification.
        value_type: The type of this specification.
        description: A description of what the specification represents.
    """

    def __init__(self, name: InterfaceName, value_type: ValueType, description: str = ""):
        self.name: InterfaceName = name
        self.value_type = value_type
        self.description: str = description

    def _to_json_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "value_type": self.value_type.value,
            "description": self.description,
        }

    @classmethod
    def _from_json(cls, data: dict[str, Any]) -> "Specification":
        if "shape" in data:
            return TensorSpecification._from_json(data)  # noqa: SLF001
        data["value_type"] = ValueType(data["value_type"])
        return cls(**data)

    @overload
    def validate_and_coerce(self: Literal[ValueType.BOOL], value: Any) -> bool: ...

    @overload
    def validate_and_coerce(self: Literal[ValueType.INT], value: Any) -> int: ...

    @overload
    def validate_and_coerce(self: Literal[ValueType.LINDBLAD], value: Any) -> PauliLindbladMap: ...

    @overload
    def validate_and_coerce(self: Literal[ValueType.NUMPY_ARRAY], value: Any) -> np.ndarray: ...

    def validate_and_coerce(self, value):
        if self.value_type is ValueType.BOOL:
            return bool(value)
        if self.value_type is ValueType.INT:
            return int(value)
        if self.value_type is ValueType.LINDBLAD:
            if isinstance(value, PauliLindbladMap):
                return value
        if self.value_type is ValueType.NUMPY_ARRAY:
            return np.array(value)
        raise TypeError(f"Object is type {type(value)} but expected {self.value_type}.")

    def __repr__(self):
        return (
            f"{type(self).__name__}({repr(self.name)}, {self.value_type.value}, "
            f"{repr(self.description)}"
        )


class TensorSpecification(Specification):
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
        super().__init__(name, ValueType.NUMPY_ARRAY, description)
        self.shape = shape
        self.dtype = dtype

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

    def empty(self) -> np.ndarray:
        """Create an empty output according to this specification.

        Args:
            num_samples: How many samples have been requested.

        Returns:
            An empty output according to this specification.
        """
        return np.empty(self.shape, dtype=self.dtype)

    def validate_and_coerce(self, value):
        value = super().validate_and_coerce(value)
        if value.dtype != self.dtype or value.shape != self.shape:
            raise SamplexInputError(
                f"Input ``{self.name}`` expects an array of shape `{self.shape}` and type "
                f"`{self.dtype}` but received {value}."
            )
        return value

    def __repr__(self):
        return (
            f"{type(self).__name__}({repr(self.name)}, {repr(self.shape)}, {repr(self.dtype)}, "
            f"{repr(self.description)}"
        )


class Interface(Mapping):
    """An interface.

    Args:
       specs: An iterable of specificaitons.
    """

    def __init__(self, specs: Iterable[Specification]):
        self.specs = {spec.name: spec for spec in specs}
        self._data: dict[InterfaceName, Any] = {}

    @property
    def fully_bound(self) -> bool:
        """Whether all the interfaces have data specified."""
        return self.specs.keys() == self._data.keys()

    @property
    def non_tensor_specs(self) -> list[Specification]:
        """The non-tensor specifications in this interface."""
        return [spec for spec in self.specs if not isinstance(spec, TensorSpecification)]

    @property
    def tensor_specs(self) -> list[TensorSpecification]:
        """The tensor specifications in this interface."""
        return [spec for spec in self.specs if isinstance(spec, TensorSpecification)]

    def bind(self, **kwargs) -> Self:
        """Bind data to an interface.

        Args:
            **kwargs: The interface to bind.

        Raises:
            ValueError: If a specification not present in this interface is in ``kwargs``.

        Returns:
            This interface."""
        for interface_name, value in kwargs.items():
            if isinstance(value, dict):
                self.bind(**{f"{interface_name}.{k}"): v for k, v in value.items()})
                continue
            if (spec := self.specs.get(interface_name)) is None:
                raise ValueError(f"No specification named {interface_name}.")
            self._data[interface_name] = spec.validate_and_coerce(value)

        return self

    def __repr__(self):
        return f"{type(self).__name__}({repr(self.specs)})"

    def __contains__(self, key):
        return key in self._data

    def __getitem__(self, key):
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)


class SamplexInput(Interface):
    """The input of a single call to :meth:`~Samplex.sample`.

    Args:
        specifiers: A specification of what is present in the input.
        defaults: A map from input names to their default values.
    """

    def __init__(self, specs: Iterable[Specification], defaults: dict[InterfaceName, Any] | None):
        super().__init__(specs)
        defaults = {} if defaults is None else defaults
        self.defaults = defaults

    @property
    def fully_bound(self) -> bool:
        values = set(self._data)
        values.union_update(self.defaults)
        return set(self.specs.keys()) == values

    def __getitem__(self, key):
        try:
            return self._data[key]
        except KeyError:
            return self.defaults[key]


class SamplexOutput(Interface):
    """The output of a single call to :meth:`~Samplex.sample`.

    Args:
        specifiers: A specification of what interfaces are present in the output.
        metadata: Information relating to the process of sampling.
    """

    def __init__(
        self, specs: Iterable[TensorSpecification], metadata: dict[str, Any] | None = None
    ):
        super().__init__(specs)
        self._data = {spec.name: spec.empty() for spec in specs}
        self.metadata: dict[str, Any] = {} if metadata is None else metadata
