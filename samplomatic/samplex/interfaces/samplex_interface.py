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

from collections.abc import Mapping
from typing import Generic, TypeVar

from ...aliases import InterfaceName

InterfaceT = TypeVar("InterfaceT")
SpecificationT = TypeVar("SpecificationT")


class InterfaceSpecification(Generic[InterfaceT]):
    """Specification of a single named interface from a samplex.

    Args:
        name: The name of the interface.
        description: A description of what the interface represents.
    """

    def __init__(self, name: InterfaceName, description: str = ""):
        self.name: InterfaceName = name
        self.description: str = description

    def __repr__(self):
        return f"{type(self).__name__}({repr(self.name)}, {repr(self.description)})"


class SamplexInterface(Mapping):
    """An interface for a call to :meth:`~Samplex.sample`.

    Args:
        specifiers: A specification of what is present in the interface.
    """

    def __contains__(self, key):
        return key in self._data

    def __getitem__(self, key):
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)
