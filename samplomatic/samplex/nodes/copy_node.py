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

"""CopyNode"""

from copy import deepcopy

from ...annotations import VirtualType
from .evaluation_node import EvaluationNode


class CopyNode(EvaluationNode):
    """Copies a register.

    Args:
        copy_registers:
        copy_prefix:
    """

    def __init__(
        self,
        register_name: str,
        output_name: str,
        output_type: VirtualType,
        num_output_subsystems: int,
    ):
        self._register_name = register_name
        self._output_name = output_name
        self._output_type = output_type
        self._num_output_subsystems = num_output_subsystems

    def instantiates(self):
        return {self._output_name: (self._num_output_subsystems, self._output_type)}

    def reads_from(self):
        return {self._register_name: (self._num_output_subsystems, self._output_type)}

    def evaluate(self, registers, *_):
        registers[self._output_name] = deepcopy(registers[self._register_name])

    def get_style(self):
        return (
            super()
            .get_style()
            .append_data("Copies", self._register_name)
            .append_data("Output Type", self._output_type.name)
            .append_data("Output Num Subsystems", self._num_output_subsystems)
        )
