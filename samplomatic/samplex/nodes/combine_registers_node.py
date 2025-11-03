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

"""CombineRegistersNode"""

from collections.abc import Sequence
from enum import Enum, auto

import numpy as np

from ...aliases import RegisterName, SubsystemIndex
from ...annotations import VirtualType
from ...exceptions import SamplexConstructionError
from ...virtual_registers import VirtualRegister
from .evaluation_node import EvaluationNode


class CombineType(Enum):
    """A helper Enum to indicate how a given register combines into the output register."""

    SET = auto()
    MULTIPLY = auto()


class CombineRegistersNode(EvaluationNode):
    """Composes one or more registers into a new register.

    The registers are composed in the order of ``operands``.

    The new register can be larger than any of the registers being composed. In this case, any slice
    of the new register that remains untouched is initialized to identity. Therefore, this node can
    be used for virtual gate multiplication of registers of the same type, for tensoring subsystems,
    for slicing registers, for implicit identity insertion, and for subsystem reordering.

    Args:
        output_type: What type of register type to collect into.
        output_register_name: The name of the output register.
        num_output_subsystems: The number of subsystems of the output register.
        operands: A map from register names to tuples
            ``(source_idxs, destination_idxs, input_type)`` where
            ``source_idxs`` slices the input register, ``destination_idxs`` is of the same
            length and slices the output register, dictating the location into which to multiply,
            and ``input_type`` is the type of the input register. The order of this map is in
            standard matrix multiplication order.

    Raises:
        SamplexConstructionError: If some pair of input and output indices don't match size.
        SamplexConstructionError: If an output index is not in ``[0, .., num_output_subsystems-1]``.
        SamplexConstructionError: If there is not at least one register.
    """

    def __init__(
        self,
        output_type: VirtualType,
        output_register_name: RegisterName,
        num_output_subsystems: int,
        operands: dict[
            RegisterName, tuple[Sequence[SubsystemIndex], Sequence[SubsystemIndex], VirtualType]
        ],
    ):
        self._output_type = output_type
        self._output_register_name = output_register_name
        self._num_output_subsystems = num_output_subsystems
        self._operands = {}
        already_set_destination_idxs = set()
        for register_name, (source_idxs, destination_idxs, input_type) in list(operands.items()):
            source_idxs = np.asarray(source_idxs, dtype=np.intp)
            destination_idxs = np.asarray(destination_idxs, dtype=np.intp)
            if (
                source_idxs.ndim != 1
                or destination_idxs.ndim != 1
                or source_idxs.size != destination_idxs.size
            ):
                raise SamplexConstructionError(
                    f"Input and output indices for '{register_name}' have the wrong shape, they "
                    f"are {source_idxs.shape} and {destination_idxs.shape} respectively."
                )
            if destination_idxs.max() >= num_output_subsystems or destination_idxs.min() < 0:
                raise SamplexConstructionError(
                    f"Output subsystem indices for '{register_name}' reference a subsystem out "
                    f"of the bounds [0, {num_output_subsystems - 1}]."
                )
            # Check against the destination idxs we already set to see if we need
            # to multiply or just set the values.
            combine_type = (
                CombineType.SET
                if already_set_destination_idxs.isdisjoint(destination_idxs)
                else CombineType.MULTIPLY
            )
            already_set_destination_idxs.update(destination_idxs)
            self._operands[register_name] = (
                source_idxs,
                destination_idxs,
                input_type,
                combine_type,
            )

        if not self._operands:
            raise SamplexConstructionError(f"{self} requires at least one input register.")

    @property
    def outgoing_register_type(self) -> VirtualType:
        return self._output_type

    def instantiates(self):
        return {self._output_register_name: (self._num_output_subsystems, self._output_type)}

    def reads_from(self):
        return {
            register_name: (set(source_idxs), input_type)
            for register_name, (source_idxs, _, input_type, _) in self._operands.items()
        }

    def validate_and_update(self, register_descriptions):
        super().validate_and_update(register_descriptions)

        for register_name in self._operands:
            _, found_type = register_descriptions[register_name]
            if self._output_type not in VirtualRegister.select(found_type).CONVERTABLE_TYPES:
                raise SamplexConstructionError(
                    f"{self} expects `{register_name}` to be convertable to type "
                    f"'{self._output_type.value}' but found '{found_type.value}'."
                )

    def evaluate(self, registers, *_):
        num_samples = max(registers.get(reg).num_samples for reg in self.reads_from())
        register_cls = VirtualRegister.select(self._output_type)
        output_register = register_cls.identity(self._num_output_subsystems, num_samples)

        # multiply together all registers, in order
        for register_name, (
            source_idxs,
            destination_idxs,
            _,
            combine_type,
        ) in self._operands.items():
            operand = registers[register_name].convert_to(self._output_type)[source_idxs]
            if combine_type is CombineType.MULTIPLY:
                output_register.inplace_multiply(operand, destination_idxs)
            else:
                output_register[destination_idxs] = operand

        registers[self._output_register_name] = output_register

    def __eq__(self, other):
        if not (
            isinstance(other, CombineRegistersNode)
            and self._output_type == other._output_type
            and self._output_register_name == other._output_register_name
            and self._num_output_subsystems == other._num_output_subsystems
            and len(self._operands) == len(other._operands)
        ):
            return False
        for reg_name, (source_idx, dest_idx, input_type, _) in self._operands.items():
            if (other_operand := other._operands.get(reg_name)) is None:
                return False
            other_source_idx, other_dest_idx, other_input_type, _ = other_operand
            if not (
                np.array_equal(source_idx, other_source_idx)
                and np.array_equal(dest_idx, other_dest_idx)
                and input_type == other_input_type
            ):
                return False
        return True

    def get_style(self):
        operands = {
            register_name: (source_idxs.tolist(), destination_idxs.tolist(), str(input_type))
            for register_name, (
                source_idxs,
                destination_idxs,
                input_type,
                _,
            ) in self._operands.items()
        }
        return (
            super()
            .get_style()
            .append_data("Output Type", self._output_type.name)
            .append_data("Output Num Subsystems", self._num_output_subsystems)
            .append_data("Operands", operands)
        )
