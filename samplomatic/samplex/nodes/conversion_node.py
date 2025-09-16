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

"""ConversionNode"""

from ...aliases import NumSubsystems, RegisterName
from ...annotations import VirtualType
from ...exceptions import SamplexConstructionError
from ...virtual_registers import VirtualRegister
from .evaluation_node import EvaluationNode


class ConversionNode(EvaluationNode):
    """Converts a node from one type to another.

    Args:
        existing_name: The name of the register to convert.
        existing_type: The type of the register to convert.
        new_name: The name of the the converted register, possibly equal to ``existing_name``.
        new_type: The type to convert to.
        num_subsystems: The number of subsystems in the register to convert.
        remove_existing: Whether to remove the existing register following conversion.

    Raises:
        SamplexConstructionError: If the names are the same, and ``remove_existing`` is true.
    """

    def __init__(
        self,
        existing_name: RegisterName,
        existing_type: VirtualType,
        new_name: RegisterName,
        new_type: VirtualType,
        num_subsystems: NumSubsystems,
        remove_existing: bool,
    ):
        self.existing_name = existing_name
        self.existing_type = existing_type
        self.new_name = new_name
        self.new_type = new_type
        self.num_subsystems = num_subsystems
        self.remove_existing = remove_existing

        if existing_name == new_name and remove_existing:
            raise SamplexConstructionError(
                f"The existing name and the new name are equal ('{self.new_name}'), but "
                "remove_existing was not set to true."
            )

    def _to_json_dict(self) -> dict[str, str]:
        return {
            "node_type": "4",
            "existing_name": self.existing_name,
            "existing_type": self.existing_type.value,
            "new_name": self.new_name,
            "new_type": self.new_type.value,
            "num_subsystems": self.num_subsystems,
            "remove_existing": str(self.remove_existing),
        }

    @classmethod
    def _from_json_dict(cls, data: dict[str, str]) -> "ConversionNode":
        return cls(
            data["existing_name"],
            VirtualType(data["existing_type"]),
            data["new_name"],
            VirtualType(data["new_type"]),
            int(data["num_subsystems"]),
            data["remove_existing"] == "True",
        )

    @property
    def outgoing_register_type(self) -> VirtualType:
        return self.new_type

    def reads_from(self):
        if self.remove_existing:
            return {}
        return {self.existing_name: (set(range(self.num_subsystems)), self.existing_type)}

    def instantiates(self) -> dict[RegisterName, tuple[NumSubsystems, VirtualType]]:
        return {self.new_name: (self.num_subsystems, self.new_type)}

    def removes(self) -> set[RegisterName]:
        return {self.existing_name} if self.remove_existing else set()

    def validate_and_update(self, register_descriptions):
        # let the parent class validation deal with the case where existing_name doesn't exist
        if self.existing_name in register_descriptions:
            existing_size, existing_type = register_descriptions[self.existing_name]
            if existing_size != self.num_subsystems:
                raise SamplexConstructionError(
                    f"When validating {self}, the size of '{self.existing_name}' is "
                    f"{existing_size} but should be {self.num_subsystems}."
                )
            if self.new_type not in VirtualRegister.select(existing_type).CONVERTABLE_TYPES:
                raise SamplexConstructionError(
                    f"When validating {self}, the register '{self.existing_name}' of type "
                    f"'{existing_type.value}' should be convertable to '{self.new_type.value}' "
                    "but is not."
                )

        super().validate_and_update(register_descriptions)

    def evaluate(self, registers, *_):
        registers[self.new_name] = registers[self.existing_name].convert_to(self.new_type)
        if self.remove_existing:
            registers.pop(self.existing_name)

    def get_style(self):
        return (
            super()
            .get_style()
            .append_data("Existing Register", repr(self.existing_name))
            .append_data("New Register", f"'{self.new_name}' ('{self.new_type}')")
            .append_data("Remove Existing", self.remove_existing)
        )
