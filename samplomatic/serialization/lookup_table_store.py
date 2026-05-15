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

"""Lookup table store for samplex serialization."""

import contextlib
import contextvars
from collections.abc import Generator

import numpy as np
import orjson

from .utils import array_from_json, array_to_json


class LookupTableStore:
    """A named store of numpy arrays for use during samplex serialization.

    Keys have the form ``"{node_type_id}:{name}"`` (e.g. ``"N13:cx"``), which scopes
    tables to node types so that different node types cannot accidentally share data.

    Node serializers should call :func:`get_lookup_table_store` to access the active store
    during serialization/deserialization, then call :meth:`register` or :meth:`lookup`.
    """

    def __init__(self) -> None:
        self._store: dict[str, np.ndarray] = {}

    def register(self, node_type_id: str, name: str, array: np.ndarray) -> str:
        """Store an array and return its key.

        Args:
            node_type_id: The serializer's type ID (e.g. ``"N13"``).
            name: A name for the table within that node type (e.g. ``"cx"``).
            array: The numpy array to store. Last-write-wins for identical keys.

        Returns:
            The key under which the array is stored (``"{node_type_id}:{name}"``).
        """
        key = f"{node_type_id}:{name}"
        self._store[key] = array
        return key

    def lookup(self, key: str) -> np.ndarray:
        """Retrieve an array by key.

        Args:
            key: The key previously returned by :meth:`register`.

        Returns:
            The stored array.

        Raises:
            KeyError: If no array is registered under ``key``.
        """
        return self._store[key]

    def __bool__(self) -> bool:
        return bool(self._store)

    def to_json(self) -> str:
        """Serialize the store to a JSON string.

        Arrays with ``np.intp`` dtype are cast to ``int64`` for portability.

        Returns:
            A JSON string encoding all stored arrays.
        """
        serialized = {}
        for key, array in self._store.items():
            # Cast np.intp to int64 for portability (np.intp is platform-dependent)
            if array.dtype == np.dtype(np.intp):
                array = array.astype(np.int64)
            serialized[key] = array_to_json(array)
        return orjson.dumps(serialized).decode("utf-8")

    @classmethod
    def from_json(cls, data: str) -> "LookupTableStore":
        """Deserialize a store from a JSON string.

        Args:
            data: A JSON string produced by :meth:`to_json`.

        Returns:
            A :class:`LookupTableStore` populated with the deserialized arrays.
        """
        store = cls()
        for key, array_json in orjson.loads(data).items():
            store._store[key] = array_from_json(array_json)  # noqa: SLF001
        return store


_LOOKUP_TABLE_STORE: contextvars.ContextVar[LookupTableStore | None] = contextvars.ContextVar(
    "_LOOKUP_TABLE_STORE", default=None
)


def get_lookup_table_store() -> LookupTableStore | None:
    """Return the active :class:`LookupTableStore`, or ``None`` if not set.

    Node serializers call this during serialization/deserialization to access the store
    without needing it passed through function arguments.
    """
    return _LOOKUP_TABLE_STORE.get()


@contextlib.contextmanager
def active_lookup_table_store(store: LookupTableStore) -> Generator[LookupTableStore, None, None]:
    """Context manager that sets ``store`` as the active :class:`LookupTableStore`.

    On exit the previous value is restored, even if an exception is raised.

    Args:
        store: The store to activate.

    Yields:
        The same ``store`` that was passed in.
    """
    token = _LOOKUP_TABLE_STORE.set(store)
    try:
        yield store
    finally:
        _LOOKUP_TABLE_STORE.reset(token)
