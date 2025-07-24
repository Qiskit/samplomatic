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

import json
from collections.abc import Sequence

import numpy as np

from ...aliases import RegisterName, SubsystemIndex
from ...annotations import VirtualType
from ...exceptions import SamplexConstructionError
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

    Raises:
        SamplexConstructionError: If ``slice_idxs`` has the wrong shape.
    """

    def __init__(
        self,
        input_type: VirtualType,
        output_type: VirtualType,
        input_register_name: RegisterName,
        output_register_name: RegisterName,
        slice_idxs: Sequence[SubsystemIndex],
    ):
        self._input_type = input_type
        self._output_type = output_type
        self._input_register_name = input_register_name
        self._output_register_name = output_register_name
        self._slice_idxs = np.asarray(slice_idxs, dtype=np.intp)

        if self._slice_idxs.ndim != 1:
            raise SamplexConstructionError(
                f"'slice_idxs' for '{input_register_name}' has a shape {self._slice_idxs.shape}, "
                "but a shape with a single axes is required."
            )

    def _to_json_dict(self) -> dict[str, str]:
        return {
            "node_type": "8",
            "input_type": self._input_type,
            "output_type": self._output_type,
            "input_register_name": self._input_register_name,
            "output_register_name": self._output_register_name,
            "slice_idxs": json.dumps(self._slice_idxs.tolist()),
        }

    @property
    def outgoing_register_type(self) -> VirtualType:
        return self._output_type

    def instantiates(self):
        return {self._output_register_name: (len(self._slice_idxs), self._output_type)}

    def reads_from(self):
        return {self._input_register_name: (set(self._slice_idxs), self._input_type)}

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
        if np.array_equal(self._slice_idxs, np.arange(converted_register.num_subsystems)):
            # No slicing required
            registers[self._output_register_name] = converted_register
        else:
            registers[self._output_register_name] = converted_register[self._slice_idxs]
