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

from collections.abc import Iterable
from typing import Any

from ..aliases import InterfaceName
from ..tensor_interface import Specification, TensorInterface, TensorSpecification


class SamplexInput(TensorInterface):
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
                f"interface. Available names are:\n{self.describe(prefix='  * ')}"
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


class SamplexOutput(TensorInterface):
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
        self.metadata: dict[str, Any] = {} if metadata is None else metadata
