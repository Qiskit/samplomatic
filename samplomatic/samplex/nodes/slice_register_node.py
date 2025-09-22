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

"""SliceRegisterNode"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from numpy.typing import ArrayLike

from ...aliases import RegisterName, SubsystemIndex
from ...annotations import VirtualType
from ...exceptions import SamplexConstructionError
from ...utils.serialization import array_from_json, array_to_json, slice_from_json, slice_to_json
from ...virtual_registers import VirtualRegister
from .evaluation_node import EvaluationNode


class SliceRegisterNode(EvaluationNode):
    """A node to slice a register.

    .. note::
        Slicing of a register can alternatively be done using a :class:`~.CombineRegistersNode`,
        providing ``operands`` of length ``1``. However, using
        :class:`~.SliceRegisterNode` is recommended because its :meth:`~.evaluate` method is
        optimized for slicing a single register.

    Args:
        input_type: The type of the input register.
        output_type: The type of the output register.
        input_register_name: The name of the input register.
        output_register_name: The name of the output register.
        slice_idxs: The indices used to slice the register.
        force_copy: Whether or not to force output register to be a copy instead of a view of
            the input register.

    Raises:
        SamplexConstructionError: If ``slice_idxs`` has the wrong shape.
    """

    def __init__(
        self,
        input_type: VirtualType,
        output_type: VirtualType,
        input_register_name: RegisterName,
        output_register_name: RegisterName,
        slice_idxs: slice | Sequence[SubsystemIndex],
        force_copy: bool = False,
    ):
        self._input_type = input_type
        self._output_type = output_type
        self._input_register_name = input_register_name
        self._output_register_name = output_register_name

        if isinstance(slice_idxs, slice):
            self._slice_idxs = slice_idxs
        else:
            slice_idxs = np.asarray(slice_idxs, dtype=np.intp)
            if slice_idxs.ndim != 1:
                raise SamplexConstructionError(
                    f"'slice_idxs' for '{input_register_name}' has a shape {slice_idxs.shape}, "
                    "but a shape with a single axes is required."
                )
            # Check if indices could be converted to a slice
            elif not force_copy:
                self._slice_idxs = get_slice_from_idxs(slice_idxs)
            else:
                self._slice_idxs = slice_idxs

    def _to_json_dict(self) -> dict[str, str]:
        if isinstance(self._slice_idxs, slice):
            is_slice = "true"
            slice_idxs = slice_to_json(self._slice_idxs)
        else:
            is_slice = "false"
            slice_idxs = array_to_json(self._slice_idxs)
        return {
            "node_type": "8",
            "input_type": self._input_type.value,
            "output_type": self._output_type.value,
            "input_register_name": self._input_register_name,
            "output_register_name": self._output_register_name,
            "slice_idxs": slice_idxs,
            "is_slice": is_slice,
        }

    @classmethod
    def _from_json_dict(cls, data: dict[str, str]) -> SliceRegisterNode:
        slice_idxs = (
            slice_from_json(data["slice_idxs"])
            if data["is_slice"] == "true"
            else array_from_json(data["slice_idxs"])
        )
        return cls(
            VirtualType(data["input_type"]),
            VirtualType(data["output_type"]),
            data["input_register_name"],
            data["output_register_name"],
            slice_idxs,
        )

    @property
    def outgoing_register_type(self) -> VirtualType:
        return self._output_type

    def instantiates(self):
        if isinstance(self._slice_idxs, slice):
            length = len(
                range(
                    self._slice_idxs.start,
                    self._slice_idxs.stop if self._slice_idxs.stop is not None else -1,
                    self._slice_idxs.step,
                )
            )
        else:
            length = len(self._slice_idxs)
        return {self._output_register_name: (length, self._output_type)}

    def reads_from(self):
        if isinstance(self._slice_idxs, slice):
            idxs_set = set(
                range(
                    self._slice_idxs.start,
                    self._slice_idxs.stop if self._slice_idxs.stop is not None else -1,
                    self._slice_idxs.step,
                )
            )
        else:
            idxs_set = set(self._slice_idxs)
        return {self._input_register_name: (idxs_set, self._input_type)}

    def validate_and_update(self, register_descriptions):
        super().validate_and_update(register_descriptions)

        _, found_type = register_descriptions[self._input_register_name]
        if self._output_type not in VirtualRegister.select(found_type).CONVERTABLE_TYPES:
            raise SamplexConstructionError(
                f"{self} expects `{self._input_register_name}` to be convertable to type "
                f"'{self._output_type}' but found '{found_type}'."
            )

    def evaluate(self, registers, *_):
        converted_register = registers[self._input_register_name].convert_to(self._output_type)
        registers[self._output_register_name] = converted_register[self._slice_idxs]


def get_slice_from_idxs(slice_idxs: ArrayLike) -> ArrayLike | slice:
    """Return a :class:`slice` object if the given indices are stridable.

    Args:
        slice_idxs: The indices to check.

    Returns:
        The provided indices, or an equivalent :class:`slice` object.
    """
    if len(slice_idxs) == 1:
        return slice(slice_idxs[0], slice_idxs[0] + 1, 1)
    else:
        step = slice_idxs[1] - slice_idxs[0]
        expected = slice_idxs[0] + step * np.arange(len(slice_idxs))

        if np.array_equal(slice_idxs, expected):
            return slice(
                int(slice_idxs[0]),
                int(slice_idxs[-1] + step) if slice_idxs[-1] + step >= 0 else None,
                int(step),
            )
    return slice_idxs
