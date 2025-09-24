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

"""ScopeNode"""

from collections.abc import Sequence

import orjson

from ...aliases import RegisterName, SubsystemIndex
from ...annotations import VirtualType
from ...exceptions import DeserializationError
from ...utils.serialization import array_from_json, array_to_json
from .evaluation_node import EvaluationNode


class ScopeNode(EvaluationNode):
    """Copies one or more registers.

    The registers are copied and have ``scope_prefix`` added to their name.

    Args:
        scope_registers:
        scope_prefix:
    """

    def __init__(
        self,
        scope_registers: dict[RegisterName, tuple[Sequence[SubsystemIndex], VirtualType]],
        scope_prefix: str,
    ):
        self._scope_registers = scope_registers
        self._scope_prefix = scope_prefix

    def _to_json_dict(self) -> dict[str, str]:
        scope_registers_dict = {}
        for key, values in self._scope_registers.items():
            value_list = []
            for v in values:
                if isinstance(v, VirtualType):
                    value_list.append({"type": v.value})
                else:
                    value_list.append({"array": array_to_json(v)})
            scope_registers_dict[key] = value_list

        return {
            "node_type": "13",
            "scope_prefix": self._scope_prefix,
            "scope_registers_dict": orjson.dumps(scope_registers_dict).decode("utf-8"),
        }

    @classmethod
    def _from_json_dict(cls, data: dict[str, str]) -> "ScopeNode":
        raw_copy_dict = orjson.loads(data["scope_registers_dict"])
        scope_registers = {}
        for name, values in raw_copy_dict.items():
            tuple_value = []
            for value in values:
                if array_str := value.get("array"):
                    tuple_value.append(array_from_json(array_str))
                elif type_str := value.get("type"):
                    tuple_value.append(VirtualType(type_str))
                else:
                    raise DeserializationError(f"Invalid Operand type {value}")

            scope_registers[name] = tuple(tuple_value)
        return cls(scope_registers, data["scope_prefix"])

    def instantiates(self):
        return {
            f"{name}_{self._scope_prefix}": (len(subsys_idxs), output_type)
            for name, (subsys_idxs, output_type) in self._scope_registers.items()
        }

    def reads_from(self):
        return {
            name: (set(subysys_idxs), input_type)
            for name, (subysys_idxs, input_type) in self._scope_registers.items()
        }

    def evaluate(self, registers, *_):
        for register_name, (subsys_idxs, _) in self._scope_registers.items():
            registers[f"{register_name}_{self._scope_prefix}"] = registers[register_name][
                subsys_idxs
            ]

    def get_style(self):
        scope_registers = {
            register_name: (source_idxs.tolist(), str(virtual_type))
            for register_name, (source_idxs, virtual_type) in self._scope_registers.items()
        }
        return super().get_style().append_data("Scope", scope_registers)
