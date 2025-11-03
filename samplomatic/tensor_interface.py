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

import abc
import re
import textwrap
from collections.abc import Iterable, Mapping, MutableMapping
from typing import Any, Generic, TypeVar

import numpy as np
from qiskit.quantum_info import PauliLindbladMap

from .aliases import InterfaceName, Self
from .serializable import Serializable

__all__ = [
    "Specification",
    "PauliLindbladMapSpecification",
    "TensorSpecification",
    "TensorInterface",
]

T = TypeVar("T")

ABSENT = object()


class Specification(Generic[T], metaclass=Serializable):
    """A specification of an expected value inside of an interface."""

    @property
    @abc.abstractmethod
    def name(self) -> InterfaceName:
        """The name of this specification."""

    @property
    @abc.abstractmethod
    def description(self) -> str:
        """A description of this specification."""

    @property
    @abc.abstractmethod
    def optional(self) -> bool:
        """Whether this is an optional specification."""

    @property
    @abc.abstractmethod
    def free_dimensions(self) -> set[str]:
        """Named dimensions whose sizes are free until an interface value binds their value.

        Within a :class:`~.TensorInterface`, all free dimensions of the same name must be
        consistently bound. This allows specification of dimensions of values that can be arbitrary,
        and that are only resolved once bound to an interface.
        """

    @abc.abstractmethod
    def describe(self) -> str:
        """Return a human-readable description of this specification."""

    @abc.abstractmethod
    def validate_and_coerce(self, value: Any) -> tuple[T, dict[str, int]]:
        """Coerce a value into a correct type if valid.

        Args:
            value: A value to validate and coerce with respect to this specification.

        Raises:
                TypeError: If the value cannot be coerced into a valid type.

        Returns:
            The coerced value, and a dictionary mapping each member of :attr:`~.free_dimensions` to
            a size implied by the ``value``.
        """


class PauliLindbladMapSpecification(Specification[PauliLindbladMap]):
    """A specification for interface values of type :class:`qiskit.quantum_info.PauliLindbladMap`.

    Args:
        name: The specification name.
        num_qubits: How many qubits the Pauli Lindblad map must act on.
        num_terms: A name for the dimensional freedom that represents the number of terms owned by
            the Pauli Lindblad map.
    """

    def __init__(self, name: InterfaceName, num_qubits: int, num_terms: str):
        self._name = name
        self.num_qubits = num_qubits
        self.num_terms = num_terms

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return (
            f"A PauliLindblad map acting on {self.num_qubits} qubits, "
            f"with '{self.num_terms}' terms."
        )

    @property
    def optional(self):
        return False

    @property
    def free_dimensions(self):
        return {self.num_terms}

    def describe(self) -> str:
        return f"'{self.name}' <PauliLindbladMap>: {self.description}"

    def validate_and_coerce(self, value):
        if not isinstance(value, PauliLindbladMap):
            raise ValueError(f"Expected a PauliLindbladMap, but received {value}.")

        if value.num_qubits != self.num_qubits:
            raise ValueError(
                f"Expected a PauliLindbladMap acting on {self.num_qubits} qubits, but received one "
                f"acting on {value.num_qubits} qubits instead."
            )

        return value, {self.num_terms: len(value)}

    def __repr__(self):
        return (
            f"{type(self).__name__}({repr(self.name)}, num_qubits={self.num_qubits}, "
            f"num_terms={self.num_terms})"
        )

    def __eq__(self, other) -> bool:
        if isinstance(other, PauliLindbladMapSpecification):
            return (
                self.name == other.name
                and self.num_terms == other.num_terms
                and self.num_qubits == other.num_qubits
            )
        return False


class TensorSpecification(Specification[np.ndarray]):
    """A specification for tensor-valued interface values of a specific type and shape.

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
        shape: tuple[int | str, ...],
        dtype: np.dtype,
        description: str = "",
        broadcastable: bool = False,
        optional: bool = False,
    ):
        self._name = name
        self._free_dimensions = {dim for dim in shape if isinstance(dim, str)}
        self.shape = tuple(dim if dim in self._free_dimensions else int(dim) for dim in shape)
        self.dtype = np.dtype(dtype)
        self.broadcastable = broadcastable
        self._description = description
        self._optional = optional

    @property
    def name(self):
        return self._name

    @property
    def optional(self):
        return self._optional

    @property
    def description(self):
        return self._description

    @property
    def free_dimensions(self):
        return set(self._free_dimensions)

    @property
    def ndim(self) -> int:
        """The number of dimensions, i.e. the length of :attr:`~shape`."""
        return len(self.shape)

    def describe(self) -> str:
        if self.broadcastable:
            shape_string = f"[*, {', '.join(map(repr, self.shape))}]"
        else:
            shape_string = repr(list(self.shape))
        optional = "(Optional) " if self.optional else ""
        return f"'{self.name}' <{self.dtype}{shape_string}>: {optional}{self.description}"

    def validate_and_coerce(self, value):
        try:
            value = np.array(value)
        except ValueError as exc:
            raise ValueError(f"Input '{self.name}' expects an array but received {value}.") from exc
        try:
            value = value.astype(self.dtype, casting="unsafe")
        except (TypeError, ValueError):
            raise ValueError(
                f"Input '{self.name}' is expected to be castable to type {self.dtype} "
                f"under the casting=unsafe rule, but got a type {value.dtype}."
            )
        if value.ndim < self.ndim:
            axis = "axes" if self.ndim > 1 else "axis"
            raise ValueError(
                f"Input '{self.name}' must have at least {self.ndim} {axis}, "
                f"but instead has shape {value.shape}."
            )
        trailing_shapes_agree = True
        bound_dimensions = {}
        for dim, value_dim in zip(self.shape, value.shape[len(value.shape) - self.ndim :]):
            if dim in self._free_dimensions:
                if dim in bound_dimensions and bound_dimensions[dim] != value_dim:
                    raise ValueError(
                        f"Input `{self.name}` has self-inconsistent values for the free dimension "
                        f"{dim}: it specifies at least the two different values {value_dim}"
                        f"and {bound_dimensions[dim]}."
                    )
                bound_dimensions[dim] = value_dim
            else:
                trailing_shapes_agree &= dim == value_dim
        if self.broadcastable:
            if not trailing_shapes_agree:
                raise ValueError(
                    f"Input '{self.name}' expects an array ending with shape {self.shape} "
                    f"but received one with shape {value.shape}."
                )
        elif not trailing_shapes_agree:
            raise ValueError(
                f"Input '{self.name}' expects an array of shape {self.shape}, "
                f"but received one with shape {value.shape} and dtype {value.dtype}."
            )
        return value, bound_dimensions

    def __repr__(self):
        description = f", '{self.description}'" if self.description else ""
        broadcastable = ", broadcastable=True" if self.broadcastable else ""
        optional = ", optional=True" if self.optional else ""
        return (
            f"{type(self).__name__}('{self.name}', {repr(self.shape)}, {repr(self.dtype)}"
            f"{description}{broadcastable}{optional})"
        )

    def __eq__(self, other) -> bool:
        if isinstance(other, TensorSpecification):
            return (
                self.name == other.name
                and self.dtype == other.dtype
                and self.shape == other.shape
                and self.broadcastable == other.broadcastable
                and self.optional == other.optional
            )
        return False


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
        self._dimension_constraints = {
            free_dimension: ABSENT
            for spec in self._specs.values()
            for free_dimension in spec.free_dimensions
        }

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
    def free_dimensions(self) -> set[str]:
        """All free dimensions in the interface."""
        return set(self._dimension_constraints)

    @property
    def bound_dimensions(self) -> dict[str, int]:
        """Those :attr:`~.free_dimensions` that have already been bound to a value."""
        return {
            free_dimension: size
            for free_dimension, size in self._dimension_constraints.items()
            if size is not ABSENT
        }

    @property
    def _unbound_specs(self) -> set[str]:
        """The specifications that do not have any data."""
        return {name for name in self._specs if name not in self._data}

    def describe(
        self,
        include_bound: bool = True,
        include_free_dimensions: bool = False,
        prefix: str = "* ",
        bound_prefix: str | None = None,
        width: int = 0,
    ) -> str:
        """Return a human-readable description of this interface.

        Args:
            include_bound: Whether to include interface specs that are already bound.
            include_free_dimensions: Whether to include information about free dimensions and
                their bound values.
            prefix: A string prefix for every specification in the interface that has no value.
            bound_prefix: A string prefix for every specification in the interface that has a value,
                or ``None`` to use the same value as ``prefix``.
            width: The text width to wrap at, minimum 40, but where 0 specifies no wrapping.

        Returns:
            A description.
        """
        bound_prefix = prefix if bound_prefix is None else bound_prefix

        ret = []
        if include_free_dimensions and (
            constraints := {
                name: val for name, val in self._dimension_constraints.items() if val is not ABSENT
            }
        ):
            constraints = ", ".join(f"{name}={val}" for name, val in sorted(constraints.items()))
            ret.append(f"{prefix}Dimension constraints: {constraints}")
            ret.append("")

        unbound = self._unbound_specs
        ret.extend(
            f"{bound_prefix if spec.name in self else prefix}{spec.describe()}"
            for spec in self._specs.values()
            if not spec.optional and (include_bound or spec.name in unbound)
        )

        if ret:
            ret.append("")

        ret.extend(
            f"{bound_prefix if spec.name in self else prefix}{spec.describe()}"
            for spec in self._specs.values()
            if spec.optional and (include_bound or spec.name in unbound)
        )

        if width >= 40:
            joiner = "\n" + " " * (len(prefix) + 2)
            for idx in range(len(ret)):
                ret[idx] = joiner.join(textwrap.wrap(ret[idx], width - len(joiner)))

        return "\n".join(ret)

    def get_specs(self, pattern: str = "") -> list[Specification]:
        """Return all specifications of this inteface whose names the pattern string.

        Args:
            pattern: A pattern string. Regex is supported.

        Returns:
            Those specifications whose names match the pattern, sorted.
        """
        regex_pattern = re.compile(pattern)
        return [spec for name, spec in self._specs.items() if regex_pattern.search(name)]

    def bind(self, **kwargs: Mapping[str, Any]) -> Self:
        """Bind data to this interface.

        A tensor interface is a flat data structure mapping names to values, where the values must
        conform to constraints specifed by the :attr:`~.specs`.

        .. plot::
            :include-source:
            :context:
            :nofigs:

            >>> from samplomatic.tensor_interface import TensorSpecification, TensorInterface
            >>> import numpy as np
            >>>
            >>> interface = TensorInterface([
            ...     TensorSpecification("foo.bar", (2, 3), np.float64),
            ...     TensorSpecification("x", (15,), np.int64),
            ...     TensorSpecification("y", (4,), np.float32)
            ... ])
            >>>
            >>> # bind a single value
            >>> interface.bind(x=np.arange(15), y=np.linspace(0, 1, 4)) # doctest: +ELLIPSIS
            TensorInterface(...)
            >>>
            >>> # bind a value that has a "."-separated name
            >>> interface.bind(foo={"bar": np.zeros((2, 3))}) # doctest: +ELLIPSIS
            TensorInterface(...)
            >>>
            >>> # alternatively, items can be set directly
            >>> interface["foo.bar"] = np.ones((2, 3))
            >>> interface["y"] = [2.1, 2.2, 2.3, 2.4]

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

    def make_broadcastable(self) -> TensorInterface:
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

    def __str__(self):
        description = self.describe(
            bound_prefix="  * ", prefix="  - ", width=100, include_free_dimensions=True
        )
        body = f"\n{description}" if self._specs else ""
        return f"{type(self).__name__}(<{body}>)"

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
            value, constraints = spec.validate_and_coerce(value)
            for free_dimension, dim_value in constraints.items():
                if (expected := self._dimension_constraints[free_dimension]) is ABSENT:
                    self._dimension_constraints[free_dimension] = dim_value
                elif expected != dim_value:
                    raise ValueError(
                        f"Inconsistent values for the free dimension '{free_dimension}': "
                        f"it specifies at least the two different values {dim_value} "
                        f"and {expected}."
                    )
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
