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

"""FrozenDict"""

from collections.abc import Mapping
from itertools import chain
from types import MappingProxyType


class FrozenDict(Mapping):
    """An immutable and hashable dictionary-like mapping.

    Keys and values must be hashable. Views onto keys, items, and values are read-only and
    preserve insertion order. Standard operands like ``|`` are supported, but return copies when
    necessary.
    """

    __slots__ = ("_data", "_proxy", "_hash")

    def __init__(self, *args, **kwargs):
        self._data = dict(*args, **kwargs)
        self._proxy = MappingProxyType(self._data)
        # hash is computed lazily
        self._hash = None

    def __getitem__(self, key):
        return self._proxy[key]

    def __iter__(self):
        return iter(self._proxy)

    def __len__(self):
        return len(self._proxy)

    def __contains__(self, key):
        return key in self._proxy

    def keys(self):
        return self._proxy.keys()

    def items(self):
        return self._proxy.items()

    def values(self):
        return self._proxy.values()

    def get(self, key, default=None):
        return self._proxy.get(key, default)

    def __setattr__(self, name, value):
        if name in self.__slots__:
            object.__setattr__(self, name, value)
        else:
            raise AttributeError(f"{type(self).__name__} is immutable.")

    def __setitem__(self, key, value):
        raise TypeError(f"{type(self).__name__} is immutable.")

    def __delitem__(self, key):
        raise TypeError(f"{type(self).__name__} is immutable.")

    def __repr__(self):
        return f"{type(self).__name__}({self._data!r})"

    def __eq__(self, other):
        if isinstance(other, FrozenDict):
            return self._data == other._data
        if isinstance(other, Mapping):
            return self._data == dict(other)
        return False

    def __hash__(self):
        if self._hash is None:
            try:
                self._hash = hash(frozenset((hash(k), hash(v)) for k, v in self._data.items()))
            except TypeError as exc:
                raise TypeError(
                    f"{type(self).__name__} is unhashable: keys and values must all be hashable."
                ) from exc
        return self._hash

    def copy(self):
        """Return ``self``, since this instance is immutable."""
        return self

    # --- Merge operators (PEP 584) ---

    def __or__(self, other):
        if not isinstance(other, Mapping):
            return NotImplemented
        return type(self)(chain(self.items(), other.items()))

    def __ror__(self, other):
        if not isinstance(other, Mapping):
            return NotImplemented
        # other's items should take precedence
        return type(self)(chain(other.items(), self.items()))

    # we can support ior by returning a new instance, instead of doing an in-place update
    __ior__ = __or__
