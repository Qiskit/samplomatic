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
        regoster_name: The name of the register to copy.
        output_name: The name of the copy register.
        register_type: The type of register to copy.
        num_subsystems: The number of subsystems the register contains.
    """

    def __init__(
        self,
        register_name: str,
        output_name: str,
        output_type: VirtualType,
        num_subsystems: int,
    ):
        self._register_name = register_name
        self._output_name = output_name
        self._output_type = output_type
        self._num_subsystems = num_subsystems

    def _to_json_dict(self) -> dict[str, str]:
        return {
            "node_type": "13",
            "register_name": self._register_name,
            "output_name": self._output_name,
            "output_type": self._output_type,
            "num_subsystems": self._num_subsystems,
        }

    @classmethod
    def _from_json_dict(cls, data: dict[str, str]) -> "CopyNode":
        return cls(
            data["register_name"],
            data["output_name"],
            VirtualType(data["output_type"]),
            int(data["num_subsystems"]),
        )

    @property
    def outgoing_register_type(self):
        return self._output_type

    def instantiates(self):
        return {self._output_name: (self._num_subsystems, self._output_type)}

    def reads_from(self):
        return {self._register_name: (set(range(self._num_subsystems)), self._output_type)}

    def evaluate(self, registers, *_):
        registers[self._output_name] = deepcopy(registers[self._register_name])

    def get_style(self):
        return (
            super()
            .get_style()
            .append_data("Copies", self._register_name)
            .append_data("Output Type", self._output_type.name)
            .append_data("Output Num Subsystems", self._num_subsystems)
        )
