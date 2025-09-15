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

"""MultiplicationNode"""

import orjson

from ...aliases import RegisterName, Self
from ...annotations import VirtualType
from ...exceptions import SamplexConstructionError
from ...virtual_registers import GroupRegister, VirtualRegister, virtual_register_from_json
from .evaluation_node import EvaluationNode


class MultiplicationNode(EvaluationNode):
    """Abstract parent for nodes that perform multiplication against a fixed register.

    Args:
        operand: The fixed group elements by which to multiply.
        register_name: The name of the register to multiply with.

    Raises:
        SamplexConstructionError: If ``operand`` has more than one sample.
    """

    def __init__(self, operand: GroupRegister, register_name: RegisterName):
        self._operand = operand
        self._register_name = register_name

        if self._operand.num_samples != 1:
            raise SamplexConstructionError(
                f"Expected fixed operand to have only one sample but it has "
                f"{self._operand.num_samples}."
            )

    @classmethod
    def _from_json_dict(cls, data: dict[str, str]) -> Self:
        operand = virtual_register_from_json(orjson.loads(data["operand"]))
        return cls(
            operand,
            data["register_name"],
        )

    @property
    def outgoing_register_type(self) -> VirtualType:
        return self._operand.TYPE

    def writes_to(self):
        return {
            self._register_name: (
                set(range(self._operand.num_subsystems)),
                self._operand.TYPE,
            )
        }

    def get_style(self):
        return super().get_style().append_data("Fixed Operand", repr(self._operand))


class LeftMultiplicationNode(MultiplicationNode):
    """Perform left multiplication of a fixed register against a given register.

    Args:
        operand: The fixed group elements by which to multiply.
        register_name: The name of the register to multiply with.

    Raises:
        SamplexConstructionError: If ``operand`` has more than one sample.
    """

    def _to_json_dict(self) -> dict[str, str]:
        return {
            "node_type": "6",
            "operand": orjson.dumps(self._operand.to_json_dict()).decode("utf-8"),
            "register_name": self._register_name,
        }

    def evaluate(self, registers: dict[RegisterName, VirtualRegister], *_):
        registers[self._register_name].left_inplace_multiply(self._operand)


class RightMultiplicationNode(MultiplicationNode):
    """Perform right multiplication of a fixed register against a given register.

    Args:
        operand: The fixed group elements by which to multiply.
        register_name: The name of the register to multiply with.

    Raises:
        SamplexConstructionError: If ``operand`` has more than one sample.
    """

    def _to_json_dict(self) -> dict[str, str]:
        return {
            "node_type": "11",
            "operand": orjson.dumps(self._operand.to_json_dict()).decode("utf-8"),
            "register_name": self._register_name,
        }

    def evaluate(self, registers: dict[RegisterName, VirtualRegister], *_):
        registers[self._register_name].inplace_multiply(self._operand)
