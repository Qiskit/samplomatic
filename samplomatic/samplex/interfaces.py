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

    def describe(self) -> str:
        """Return a human-readable description of this specification."""
        return f"'{self.name}' ({self.value_type.value}): {self.description}"

    @overload
    def validate_and_coerce(self: Literal[ValueType.BOOL], value: Any) -> bool: ...

    @overload
    def validate_and_coerce(self: Literal[ValueType.INT], value: Any) -> int: ...

    @overload
    def validate_and_coerce(self: Literal[ValueType.LINDBLAD], value: Any) -> PauliLindbladMap: ...

    @overload
    def validate_and_coerce(self: Literal[ValueType.NUMPY_ARRAY], value: Any) -> np.ndarray: ...

    def validate_and_coerce(self, value):
        """Coerce values into correct type if valid.

        Args:
            value: A value to validate and coerce with respect to this specification.

        Raises:
                TypeError: If the value cannot be coerced into a valid type.

        Returns:
            The coerced value.
        """
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
        self, name: InterfaceName, shape: tuple[int, ...], dtype: np.dtype, description: str = ""
    ):
        super().__init__(name, ValueType.NUMPY_ARRAY, description)
        self.shape = shape
        self.dtype = dtype

    def _to_json_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "dtype": str(self.dtype),
            "shape": tuple(int(x) for x in self.shape),
        }

    @classmethod
    def _from_json(cls, data: dict[str, Any]) -> "TensorSpecification":
        return cls(data["name"], tuple(data["shape"]), np.dtype(data["dtype"]), data["description"])

    def describe(self) -> str:
        """Return a human-readable description of this specification."""
        return f"'{self.name}' ({self.dtype}{list(self.shape)}): {self.description}"

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
                f"Input '{self.name}' expects an array of shape {self.shape} and dtype "
                f"{self.dtype} but received one with shape {value.shape} and dtype {value.dtype}."
            )
        return value

    def __repr__(self):
        return (
            f"{type(self).__name__}({repr(self.name)}, {repr(self.shape)}, {repr(self.dtype)}, "
            f"{repr(self.description)}"
        )


class Interface(Mapping):
    """An interface described by strict value type specifications.

    This object implements the mapping protocol against data that is present; if a possible
    value type has a :class:`~.Specification`, it is not reported as being present
    (i.e. ``"name" in interface``) until a value has been assigned to it. Assigning to a key
    without a specification, or an invalid value to a specified key, will raise an error.

    Args:
       specs: An iterable of specificaitons for the allowed data in this interface.
    """

    def __init__(self, specs: Iterable[Specification]):
        self._specs = {spec.name: spec for spec in sorted(specs, key=lambda spec: spec.name)}
        self._data: dict[InterfaceName, Any] = {}

    @property
    def fully_bound(self) -> bool:
        """Whether all the interfaces have data specified."""
        return self._specs.keys() == self._data.keys()

    @property
    def specs(self) -> list[Specification]:
        """The interface specifacations, sorted by name."""
        return list(self._specs.values())

    @property
    def _unbound_specs(self) -> set[str]:
        """The specifications that do not have any data."""
        return {name for name in self._specs if name not in self._data}

    def describe(self, include_bound: bool = True, prefix: str = "") -> str:
        """Return a human-readable description of this interface.

        Args:
            include_bound: Whether to include interface specs that are already bound.
            prefix: A string prefix for every line returned.

        Returns:
            A description.
        """
        unbound = self._unbound_specs
        ret = [
            f"{prefix} * {spec.describe()}"
            for spec in self._specs.values()
            if isinstance(spec, TensorSpecification) and (include_bound or spec.name in unbound)
        ]

        if ret:
            ret.append("")

        ret.extend(
            f"{prefix} * {spec.describe()}"
            for spec in self._specs.values()
            if not isinstance(spec, TensorSpecification) and (include_bound or spec.name in unbound)
        )

        return "\n".join(ret)

    def bind(self, **kwargs) -> Self:
        """Bind data to this interface.

        Args:
            **kwargs: Key-value data to bind.

        Raises:
            ValueError: If a specification not present in this interface is in ``kwargs``.

        Returns:
            This interface.
        """
        for interface_name, value in kwargs.items():
            self[interface_name] = value

        return self

    def __repr__(self):
        return f"{type(self).__name__}({repr(self._specs)})"

    def __contains__(self, key):
        return key in self._data

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        if isinstance(value, dict):
            for name, subvalue in value.items():
                self[f"{key}.{name}"] = subvalue
        elif (spec := self._specs.get(key)) is None:
            raise ValueError(
                f"The interface has no specification named '{key}'. "
                f"Only the following interface names are allowed:\n{self.describe(prefix='  ')}"
            )
        else:
            self._data[key] = spec.validate_and_coerce(value)

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)


class SamplexInput(Interface):
    """The input of a single call to :meth:`~Samplex.sample`.

    Args:
        specs: An iterable of specificaitons for the allowed data in this interface.
        defaults: A map from input names to their default values.
    """

    def __init__(self, specs: Iterable[Specification], defaults: dict[InterfaceName, Any] | None):
        super().__init__(specs)
        defaults = {} if defaults is None else defaults
        self.defaults = defaults

    @property
    def fully_bound(self):
        values = set(self._data)
        values.update(self.defaults)
        return set(self._specs) == values

    @property
    def _unbound_specs(self) -> set[str]:
        # override to consider items with defaults bound
        return {
            name for name in self._specs if name not in self._data and name not in self.defaults
        }

    def __getitem__(self, key):
        if key not in self._specs:
            raise KeyError(
                f"'{key}' does not correspond to a specification present in this "
                f"interface. Available names are:\n{self.describe(prefix='  ')}"
            )
        try:
            return self._data[key]
        except KeyError:
            try:
                return self.defaults[key]
            except KeyError:
                raise KeyError(
                    f"'{key}' has not yet had any data assigned and has no default value."
                )

    def __contains__(self, key):
        return key in self._data or key in self.defaults


class SamplexOutput(Interface):
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
