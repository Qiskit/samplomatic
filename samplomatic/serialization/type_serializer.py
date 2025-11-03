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

"""TypeSerializer"""

from __future__ import annotations

import abc
import inspect
from typing import Any, Callable, ClassVar, Generic, TypeVar

from ..exceptions import SerializationError
from ..serializable import Serializable
from ..ssv import SSV

T = TypeVar("T")


class DataSerializer(Generic[T]):
    """Abstraction for a single samplex serialization version (SSV) of some specific type.

    A :class:`~.TypeSerializer` should contain one :class:`~.DataSerializer` for every contiguous
    range of SSVs that share a format.
    """

    MIN_SSV: ClassVar[int] = None
    """The minimum SSV for which this serializer is valid."""

    MAX_SSV: ClassVar[int | None] = None
    """The maximum SSV for which this serializer is valid.

    A ``None`` value indicates validitity up to and including the most recent :var:`SSV`.
    """

    @classmethod
    @abc.abstractmethod
    def serialize(self, obj: T) -> dict[str, str]:
        """Serialize into a simple dictionary.

        Args:
            obj: The object to serialize.

        Returns:
            A complete representation of ``obj`` as a dictionary mapping strings to strings.
        """

    @classmethod
    @abc.abstractmethod
    def deserialize(self, data: dict[str, str]) -> T:
        """Deserialize a simple dictionary.

        Args:
            data: The data to deserialize.

        Returns:
            A new object.
        """


class TypeSerializerMeta(type):
    """The metaclass of :class:`~.TypeSerializer`.

    This metaclass does book-keeping to help avoid misspecified identifiers and versioning. For
    example, it prevents two type serializers from declaring the same type id. A :class:`TypeError`
    will be raised at import time if such an inconsistency exists.

    It moreover collects all serialization and deserialization methods into dictionaries against
    the SSV both for convenience to speed up dispatch and compatibility checks.
    """

    def __new__(mcls, name, bases, namespace):
        cls = super().__new__(mcls, name, bases, namespace)
        if cls.__name__ != "TypeSerializer":
            if cls.TYPE_ID is None:
                raise TypeError(
                    f"Cannot create a new TypeSerializer ({cls.__name__}) without a type id."
                )
            if cls.TYPE is None:
                raise TypeError(
                    f"Cannot create a new TypeSerializer ({cls.__name__}) without a type."
                )
            if cls.TYPE_ID in cls.TYPE_ID_REGISTRY:
                raise TypeError(
                    f"Cannot create a new TypeSerializer ({cls.__name__}) with the existing type "
                    f"id {cls.TYPE_ID}."
                )
            cls.SERIALIZERS = {}
            cls.DESERIALIZERS = {}

            for attr_name, attr_value in namespace.items():
                if inspect.isclass(attr_value) and issubclass(attr_value, DataSerializer):
                    if (min_ssv := attr_value.MIN_SSV) is None:
                        raise TypeError(f"{cls.__name__}.{attr_name} must specify a MIN_SSV.")
                    max_ssv = SSV if attr_value.MAX_SSV is None else attr_value.MAX_SSV
                    ssv_range = set(range(min_ssv, max_ssv + 1))
                    if not ssv_range.isdisjoint(cls.SERIALIZERS):
                        raise TypeError(
                            f"{cls.__name__}.{attr_name} declares multiple serializers for "
                            f"SSVs in {sorted(ssv_range.intersection(cls.SERIALIZERS))}."
                        )

                    for ssv in sorted(ssv_range):
                        cls.SERIALIZERS[ssv] = attr_value.serialize
                        cls.DESERIALIZERS[ssv] = attr_value.deserialize

            cls.SSVS = sorted(cls.SERIALIZERS)
            if cls.SSVS:
                cls.MIN_SSV = min(cls.SSVS)
                cls.MAX_SSV = max(cls.SSVS)
                if set(cls.SSVS) != set(range(cls.MIN_SSV, cls.MAX_SSV + 1)):
                    raise TypeError(f"{cls.__name__} is missing a data serializer.")

            cls.TYPE_REGISTRY[cls.TYPE] = cls.TYPE_ID
            cls.TYPE_ID_REGISTRY[cls.TYPE_ID] = cls
        return cls


class TypeSerializer(Generic[T], metaclass=TypeSerializerMeta):
    """A versioned serializer for a specific Python type.

    Every type serializer is responsible for serializing a specific type into a ``dict[str, str]``
    representation.
    """

    TYPE_ID_REGISTRY: dict[str, type[TypeSerializer]] = {}
    """A registry of all :class:`~.TypeSerializer` subclasses, mapping type ids to classes."""

    TYPE_REGISTRY: dict[Serializable, str] = {}
    """A registry of all :class:`~Serializable` types with serializers, mapping types to type ids.

    This is decoupled from the :attr:`~TYPE_ID_REGISTRY` to support multiple type ids for the same
    object when there are breaking changes.
    """

    TYPE_ID: ClassVar[str] = None
    """The type id of this serializer."""

    TYPE: ClassVar[Serializable] = None
    """The type this serializer serializers."""

    SERIALIZERS: ClassVar[dict[int, Callable[[T], dict[str, str]]]] = None
    """A map from SSVs to corresponding serialization methods."""

    DESERIALIZERS: ClassVar[dict[int, Callable[[dict[str, str]], T]]] = None
    """A map from SSVs to corresponding deserialization methods."""

    MIN_SSV: ClassVar[int | None] = None
    """The smallest SSV supported by this samplomatic package version, or none for no support."""

    MAX_SSV: ClassVar[int | None] = None
    """The largest SSV supported by this samplomatic package version, or none for no support."""

    SSVS: ClassVar[list[int]] = None
    """All SSVs supported by this samplomatic package version."""

    @classmethod
    def serialize(cls, obj: T, ssv: int | None = None) -> dict[str, str]:
        """Serialize the given object into the given SSV.

        Args:
            obj: The object to serialize.
            ssv: The SSV to use.

        Returns:
            The serialized object.

        Raises:
            SerializationError: If serialization is not supported for the given SSV.
        """
        ssv = ssv if ssv is not None else SSV
        try:
            serializer = cls.SERIALIZERS[ssv]
        except KeyError as exc:
            if ssv < cls.MIN_SSV:
                raise SerializationError(
                    f"Expected an SSV greater than or equal to {cls.MIN_SSV}, got {ssv}."
                ) from exc
            if ssv > cls.MAX_SSV:
                raise SerializationError(
                    f"Expected an SSV less than or equal to {cls.MAX_SSV}, got {ssv}."
                ) from exc
            raise SerializationError(
                f"Received invalid SSV {ssv} while serializng, it should be in the range "
                f"{cls.MIN_SSV} to {cls.MAX_SSV} inclusive."
            ) from exc
        return {
            "id": cls.TYPE_ID,
            "ssv": str(ssv),
            **serializer(obj),
        }

    @staticmethod
    def deserialize(data: dict[str, str]) -> Any:
        """Deserialize the given object.

        Args:
            data: The data to deserialize.

        Returns:
            A new object.

        Raises:
            DeserializationError: If deserialization cannot be performed.
        """
        try:
            cls = TypeSerializer.TYPE_ID_REGISTRY[data["id"]]
        except KeyError:
            raise SerializationError("Cannot deserialize object without a type id.")
        try:
            deserializer = cls.DESERIALIZERS[int(data["ssv"])]
        except KeyError as exc:
            ssv = int(data["ssv"])
            if ssv < cls.MIN_SSV:
                raise SerializationError(
                    f"Cannot deserialize an object with SSV {ssv}, the minimum supported by this "
                    f"serializer is {cls.MIN_SSV}."
                ) from exc
            if ssv > cls.MAX_SSV:
                raise SerializationError(
                    f"Cannot deserialize an object with SSV {ssv}, the maximum supported by this "
                    f"serializer is {cls.MAX_SSV}."
                ) from exc
            raise SerializationError(
                f"Received invalid SSV {ssv} while deserializng, it should be in the range "
                f"{cls.MIN_SSV} to {cls.MAX_SSV} inclusive."
            ) from exc
        return deserializer(data)
