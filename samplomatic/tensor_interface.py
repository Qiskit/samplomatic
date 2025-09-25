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

import textwrap
from collections.abc import Iterable, MutableMapping
from enum import Enum
from typing import Any, Literal, overload

import numpy as np
from qiskit.quantum_info import QubitSparsePauliList

from .aliases import InterfaceName, Self

__all__ = ["ValueType", "Specification", "TensorSpecification", "TensorInterface"]


class ValueType(str, Enum):
    """Valid types for an interface value."""

    BOOL = "bool"
    INT = "int"
    PAULIS = "paulis"
    NUMPY_ARRAY = "numpy_array"


class Specification:
    """A specification of an expected value inside of an interface.

    Args:
        name: The name of the specification.
        value_type: The type of this specification.
        description: A description of what the specification represents.
        optional: Whether the specification is optional.
    """

    def __init__(
        self, name: InterfaceName, value_type: ValueType, description: str = "", optional=False
    ):
        self.name: InterfaceName = name
        self.value_type = value_type
        self.description: str = description
        self.optional: bool = optional

    def _to_json_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "value_type": self.value_type.value,
            "description": self.description,
            "optional": self.optional,
        }

    @classmethod
    def _from_json(cls, data: dict[str, Any]) -> "Specification":
        if "shape" in data:
            return TensorSpecification._from_json(data)  # noqa: SLF001
        data["value_type"] = ValueType(data["value_type"])
        return cls(**data)

    def describe(self) -> str:
        """Return a human-readable description of this specification."""
        optional = "(Optional) " if self.optional else ""
        return f"'{self.name}' <{self.value_type.value}>: {optional}{self.description}"

    @overload
    def validate_and_coerce(self: Literal[ValueType.BOOL], value: Any) -> bool: ...

    @overload
    def validate_and_coerce(self: Literal[ValueType.INT], value: Any) -> int: ...

    @overload
    def validate_and_coerce(
        self: Literal[ValueType.PAULIS], value: Any
    ) -> QubitSparsePauliList: ...

    @overload
    def validate_and_coerce(self: Literal[ValueType.NUMPY_ARRAY], value: Any) -> np.ndarray: ...

    def validate_and_coerce(self, value):
        """Coerce a value into a correct type if valid.

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
        if self.value_type is ValueType.PAULIS:
            if isinstance(value, QubitSparsePauliList):
                return value
        if self.value_type is ValueType.NUMPY_ARRAY:
            return np.array(value)
        raise TypeError(f"Object is type {type(value)} but expected {self.value_type}.")

    def __repr__(self):
        desc = f", '{self.description}'" if self.description else ""
        optional = ", optional=True" if self.optional else ""
        return f"{type(self).__name__}({repr(self.name)}, {self.value_type.value}{desc}{optional})"


class TensorSpecification(Specification):
    """Specification of a single named tensor interface.

    Args:
        name: The name of the interface.
        shape: The shape of the input array.
        dtype: The data type of the array.
        description: A description of what the interface represents.
        broadcastable: Whether values in an interface that are constrained by this
            specification are allowed to be broadcastable with other broadcastable values in the
            same interface.
        optional: Whether the specification is optional.
    """

    def __init__(
        self,
        name: InterfaceName,
        shape: tuple[int, ...],
        dtype: np.dtype,
        description: str = "",
        broadcastable: bool = False,
        optional: bool = False,
    ):
        super().__init__(name, ValueType.NUMPY_ARRAY, description, optional)
        self.shape = tuple(map(int, shape))
        self.dtype = dtype
        self.broadcastable = broadcastable

    @property
    def ndim(self) -> int:
        """The number of dimensions, i.e. the length of :attr:`~shape`."""
        return len(self.shape)

    def _to_json_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "dtype": str(self.dtype),
            "shape": tuple(int(x) for x in self.shape),
            "broadcastable": self.broadcastable,
            "optional": self.optional,
        }

    @classmethod
    def _from_json(cls, data: dict[str, Any]) -> "TensorSpecification":
        return cls(
            data["name"],
            tuple(data["shape"]),
            np.dtype(data["dtype"]),
            data["description"],
            data["broadcastable"],
            data["optional"],
        )

    def describe(self) -> str:
        """Return a human-readable description of this specification."""
        if self.broadcastable:
            shape_string = f"[*, {', '.join(map(str, self.shape))}]"
        else:
            shape_string = str(list(self.shape))
        optional = "(Optional) " if self.optional else ""
        return f"'{self.name}' <{self.dtype}{shape_string}>: {optional}{self.description}"

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
        if value.dtype != self.dtype:
            raise ValueError(
                f"Input '{self.name}' expects an array of dtype "
                f"{self.dtype}, but received one with dtype {value.dtype}."
            )
        if self.broadcastable:
            if value.shape[len(value.shape) - self.ndim :] != self.shape:
                raise ValueError(
                    f"Input '{self.name}' expects an array ending with shape {self.shape} "
                    f"but received one with shape {value.shape}."
                )
        elif value.shape != self.shape:
            raise ValueError(
                f"Input '{self.name}' expects an array of shape {self.shape}, "
                f"but received one with shape {value.shape} and dtype {value.dtype}."
            )
        return value

    def __repr__(self):
        return super().__repr__()[:-1] + (", broadcastable=True)" if self.broadcastable else ")")


class TensorInterface(MutableMapping):
    """An interface described by strict value type specifications, with a focus on tensor values.

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
        self._shape = ()

    @property
    def fully_bound(self) -> bool:
        """Whether all non-optional interfaces have data specified."""
        required_keys = set(spec for spec, val in self._specs.items() if not val.optional)
        return required_keys.issubset(self._data)

    @property
    def shape(self) -> tuple[int, ...]:
        """The shape of this interface broadcasted over all present broadcastable tensor values.

        This shape does not include the native shapes of any particular tensor value. For example,
        if some broadastable value has shape ``(4, 5, 6, 7)`` and the associated tensor
        specification has shape ``(6, 7)``, then this value naturally contributes a shape of
        ``(4, 5)`` to this interface. Consequently, the shape here will always be ``()`` for an
        interface with no broadcastable specifications.
        """
        return self._shape

    @property
    def size(self) -> int:
        """The total number of elements once broadcasted, i.e. the product of the :attr:`~shape`."""
        return int(np.prod(self.shape, dtype=int))

    @property
    def ndim(self) -> int:
        """The number of dimensions, i.e. the length of :attr:`~shape`."""
        return len(self.shape)

    @property
    def specs(self) -> list[Specification]:
        """The interface specifacations, sorted by name."""
        return list(self._specs.values())

    @property
    def _unbound_specs(self) -> set[str]:
        """The specifications that do not have any data."""
        return {name for name in self._specs if name not in self._data}

    def describe(self, include_bound: bool = True, prefix: str = "* ", width: int = 0) -> str:
        """Return a human-readable description of this interface.

        Args:
            include_bound: Whether to include interface specs that are already bound.
            prefix: A string prefix for every line returned.
            width: The text width to wrap at, minimum 40, but where 0 specifies no wrapping.

        Returns:
            A description.
        """
        unbound = self._unbound_specs
        ret = [
            f"{prefix}{spec.describe()}"
            for spec in self._specs.values()
            if isinstance(spec, TensorSpecification) and (include_bound or spec.name in unbound)
        ]

        if ret:
            ret.append("")

        ret.extend(
            f"{prefix}{spec.describe()}"
            for spec in self._specs.values()
            if not isinstance(spec, TensorSpecification) and (include_bound or spec.name in unbound)
        )

        if width >= 40:
            joiner = "\n" + " " * (len(prefix) + 2)
            for idx in range(len(ret)):
                ret[idx] = joiner.join(textwrap.wrap(ret[idx], width - len(joiner)))

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

    def make_broadcastable(self) -> "TensorInterface":
        """Return a new interface like this one where all tensor specifications are broadcastable.

        Returns:
            A new :class:`~.TensorInterface`.
        """
        return TensorInterface(
            TensorSpecification(
                spec.name, spec.shape, spec.dtype, spec.description, True, spec.optional
            )
            if isinstance(spec, TensorSpecification)
            else spec
            for spec in self.specs
        ).bind(**self._data)

    def __repr__(self):
        return f"{type(self).__name__}({repr(self._specs)})"

    def __contains__(self, key):
        return key in self._data

    def __delitem__(self, key):
        del self._data[key]

    def __getitem__(self, key):
        if isinstance(key, str):
            return self._data[key]

        # we slice every broadcastable array according to the key
        new_values = {}
        for name, value in self.items():
            if isinstance(spec := self._specs[name], TensorSpecification) and spec.broadcastable:
                value = np.broadcast_to(value, self.shape + value.shape[value.ndim - spec.ndim :])
                new_values[name] = value[key]
            else:
                new_values[name] = value
        return TensorInterface(self.specs).bind(**new_values)

    def __setitem__(self, key, value):
        if isinstance(value, dict):
            for name, subvalue in value.items():
                self[f"{key}.{name}"] = subvalue
        elif (spec := self._specs.get(key)) is None:
            raise ValueError(
                f"The interface has no specification named '{key}'. "
                f"Only the following interface names are allowed:\n{self.describe(prefix='  * ')}"
            )
        else:
            value = spec.validate_and_coerce(value)
            if isinstance(spec, TensorSpecification) and spec.broadcastable:
                value_shape = value.shape[: value.ndim - len(spec.shape)]
                try:
                    self._shape = np.broadcast_shapes(self._shape, value_shape)
                except ValueError as exc:
                    raise ValueError(
                        f"Cannot set '{key}' to a value with shape {value.shape} because it "
                        f"is not broadcastable with the current interface shape, {self._shape}."
                    ) from exc
            self._data[spec.name] = value

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)
