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

import abc
import inspect
from typing import Any, Callable, ClassVar, Generic, TypeVar

T = TypeVar("T")


class SerializationError(Exception):
    """"""


class DataSerializer(Generic[T]):
    TSV: ClassVar[int] = None

    @classmethod
    @abc.abstractmethod
    def serialize(self, obj: T) -> dict[str, str]:
        pass

    @classmethod
    @abc.abstractmethod
    def deserialize(self, obj: dict[str, str]) -> T:
        pass


class TypeSerializerMeta(type):
    def __new__(mcls, name, bases, namespace):
        cls = super().__new__(mcls, name, bases, namespace)
        if cls.__name__ != "TypeSerializer":
            if cls.TYPE_ID is None:
                raise TypeError(
                    f"Cannot create a new TypeSerializer ({cls.__name__}) without a type id."
                )
            if cls.TYPE_ID in cls.TYPE_ID_REGISTRY:
                raise TypeError(
                    f"Cannot create a new TypeSerializer ({cls.__name__}) with the existing type "
                    f"id {cls.TYPE_ID}"
                )
            cls.SERIALIZERS = {}
            cls.DESERIALIZERS = {}

            for attr_name, attr_value in namespace.items():
                if inspect.isclass(attr_value) and issubclass(attr_value, DataSerializer):
                    if (tsv := attr_value.TSV) is None:
                        raise TypeError(f"{cls.__name__}.{attr_name} that does not specify a TSV.")
                    if not isinstance(tsv, int) or tsv < 1:
                        raise TypeError(f"{cls.__name__}.{attr_name} specifies invalid TSV, {tsv}.")
                    if tsv in cls.SERIALIZERS:
                        raise TypeError(
                            f"{cls.__name__}.{attr_name} cannot reuse the existing TSV {tsv}."
                        )
                    cls.SERIALIZERS[tsv] = attr_value.serialize
                    cls.DESERIALIZERS[tsv] = attr_value.deserialize

            if cls.SERIALIZERS:
                cls.MIN_TSV = min(cls.SERIALIZERS)
                cls.MAX_TSV = max(cls.SERIALIZERS)
                if set(cls.SERIALIZERS) != range(cls.MIN_TSV, cls.MAX_TSV + 1):
                    raise TypeError(f"{cls.__name__} is missing a data serializer.")

            cls.TYPE_ID_REGISTRY[cls.TYPE_ID] = cls
        return cls


class TypeSerializer(Generic[T], metaclass=TypeSerializerMeta):
    TYPE_ID_REGISTRY: dict[str, type["TypeSerializer"]] = {}

    TYPE_ID: ClassVar[str] = None
    SERIALIZERS: ClassVar[dict[int, Callable[[T], dict[str, str]]]] = None
    DESERIALIZERS: ClassVar[dict[int, Callable[[dict[str, str]], T]]] = None
    MIN_TSV: ClassVar[int] = None
    MAX_TSV: ClassVar[int] = None

    @classmethod
    def serialize(cls, obj: T, tsv: int | None = None) -> dict[str, str]:
        tsv = tsv or cls.MAX_TSV
        try:
            serializer = cls.SERIALIZERS[tsv]
        except KeyError as exc:
            if tsv is None:
                raise SerializationError() from exc
            if tsv < cls.MIN_TSV:
                raise SerializationError() from exc
            if tsv > cls.MAX_TSV:
                raise SerializationError() from exc
            raise SerializationError() from exc
        return {
            "id": cls.TYPE_ID,
            "tsv": str(tsv),
            **serializer(obj),
        }

    @staticmethod
    def deserialize(data: dict[str, str]) -> Any:
        try:
            cls = TypeSerializer.TYPE_ID_REGISTRY[data["id"]]
        except KeyError:
            raise
        try:
            deserializer = cls.DESERIALIZERS[int(data["tsv"])]
        except KeyError as exc:
            tsv = int(data["tsv"])
            if tsv < cls.MIN_TSV:
                raise SerializationError() from exc
            if tsv > cls.MAX_TSV:
                raise SerializationError() from exc
            raise SerializationError() from exc
        return deserializer(data)


class Foo:
    pass


class FooSerializer(TypeSerializer[Foo]):
    TYPE_ID = "0"

    class SchemaV1(DataSerializer[Foo]):
        TSV = 1

        @classmethod
        def deserialize(cls, data):
            return Foo()

        @classmethod
        def serialize(cls, obj):
            return {}
