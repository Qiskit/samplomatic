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

"""Node"""

from __future__ import annotations

import abc
import inspect
from numbers import Number
from typing import Literal

from ...aliases import InterfaceName, NumSubsystems, ParamIndex, RegisterName, Self, SubsystemIndex
from ...annotations import VirtualType
from ...exceptions import SamplexConstructionError
from ...visualization.hover_style import NodeStyle


class NodeType(abc.ABCMeta):
    """Metaclass used for registering all non-abstract subclasses.

    This is done so that we can automate testing coverage of Node serialization: there is a test
    that demands each node type does a round-trip.
    """

    def __new__(mcls, name, bases, namespace):
        cls = super().__new__(mcls, name, bases, namespace)
        if cls.__name__ != "Node" and not inspect.isabstract(cls):
            cls.NODE_REGISTRY.add(cls)
        return cls


class Node(metaclass=NodeType):
    """Parent class for samplex node operations."""

    NODE_REGISTRY: set[type[Node]] = set()

    def __repr__(self):
        register_names = sorted(f"{register_name}(r)" for register_name in self.reads_from())
        register_names.extend(f"{register_name}(w)" for register_name in sorted(self.writes_to()))
        register_names.extend(f"+{register_name}" for register_name in sorted(self.instantiates()))
        register_names.extend(f"-{register_name}" for register_name in sorted(self.removes()))
        return f"{type(self).__name__}(<{', '.join(register_names)}>)"

    @property
    def parameter_idxs(self) -> list[ParamIndex]:
        """Which evaluated parameter expressions this node needs access to at sampling time."""
        return []

    @property
    def num_parameters(self) -> int:
        """The number of parameter values this node requires at sampling time."""
        return len(self.parameter_idxs)

    @property
    def outgoing_register_type(self) -> VirtualType | None:
        """The virtual gate type of outgoing registers."""
        return None

    def outputs_to(self) -> set[InterfaceName]:
        """Return the set of names of outputs this node mutates."""
        return set()

    def reads_from(self) -> dict[RegisterName, tuple[set[SubsystemIndex], VirtualType]]:
        """Return a manifest of which virtual register values this node needs to read from."""
        return {}

    def writes_to(self) -> dict[RegisterName, tuple[set[SubsystemIndex], VirtualType]]:
        """Return a manifest of which virtual register values this node needs to write to."""
        return {}

    def instantiates(self) -> dict[RegisterName, tuple[NumSubsystems, VirtualType]]:
        """Return a manifest of new virtual registers that this node instantiates.

        .. note::
            * To change the type or size of a register, both instantiate and remove it.
            * Do not specify :meth:`~reads_from` or :meth:`~writes_to` for an instantiated register,
              these powers are implicit.
        """
        return {}

    def removes(self) -> set[RegisterName]:
        """Return a manifest of virtual registers that this node removes.

        It is assumed that registers are removed as a last step; it is not ill-defined to read
        and write from a removed register.
        """
        return set()

    def _validate_read_write(self, register_descriptions, read_or_write: Literal["read", "write"]):
        preposition = "from" if read_or_write == "read" else "to"
        access = self.reads_from() if read_or_write == "read" else self.writes_to()

        for register_name, (subsys_idxs, register_type) in access.items():
            if register_name not in register_descriptions:
                raise SamplexConstructionError(
                    f"Node {self} expected to be able to {read_or_write} {preposition} register "
                    f"'{register_name}', but the register was not found."
                )
            num_subsystems, existing_register_type = register_descriptions[register_name]
            if (max_subsys := max(subsys_idxs)) >= num_subsystems:
                raise SamplexConstructionError(
                    f"Node {self} expected register '{register_name}' to have at least "
                    f"{max_subsys + 1} subsystems for {read_or_write} access but found that it "
                    f"only has {num_subsystems}."
                )
            if register_type is not existing_register_type:
                raise SamplexConstructionError(
                    f"Node {self} expected register '{register_name}' to have type "
                    f"'{register_type.value}' for {read_or_write} access but found that it "
                    f"has type '{existing_register_type.value}'."
                )

    def validate_and_update(
        self, register_descriptions: dict[RegisterName, tuple[NumSubsystems, VirtualType]]
    ):
        """Validate provided register descriptions are compatible, update with changes.

        This method can be used by a samplex to determine when a node execution order has
        well-defined dependencies before sampling begins.

        Args:
            register_descriptions: A map from existing register names to their size and type.
        """
        self._validate_read_write(register_descriptions, "read")
        self._validate_read_write(register_descriptions, "write")

        for register_name in (removes := self.removes()):
            if register_name not in register_descriptions:
                raise SamplexConstructionError(
                    f"Node {self} removes the register '{register_name}', but no register with "
                    "that name exists."
                )

        for register_name in (instantiates := self.instantiates()):
            if register_name in removes:
                # this case allows a node to change the size/type of a register while persisting the
                # name, which is useful for type-casting nodes
                continue
            if register_name in register_descriptions:
                raise SamplexConstructionError(
                    f"Node {self} instantiates the register '{register_name}', but a register with "
                    "that name already exists."
                )

        # we have finished validating, proceed to  update the descriptions
        for register_name, (size, register_type) in instantiates.items():
            register_descriptions[register_name] = (size, register_type)

        for register_name in removes:
            if register_name not in instantiates:
                register_descriptions.pop(register_name)

    def get_style(self) -> NodeStyle:
        """Return the style of this node when plotted."""
        style = NodeStyle(title=repr(self))
        if reads_from := self.reads_from():
            style.append_dict_data("reads_from", _reg_style(reads_from), bullet="• ")
        if writes_to := self.writes_to():
            style.append_dict_data("writes_to", _reg_style(writes_to), bullet="• ")
        if instantiates := self.instantiates():
            style.append_dict_data("instantiates", _reg_style(instantiates), bullet="• ")
        if removes := self.removes():
            style.append_list_data("removes", sorted(removes), bullet="• ")
        if isinstance(outputs := self.outputs_to(), dict):
            style.append_dict_data("outputs_to", _reg_style(outputs), bullet="• ")
        return style.append_divider()

    def _to_json_dict(self) -> dict[str, str]:
        raise NotImplementedError

    @classmethod
    def _from_json_dict(cls, data: dict[str, str]) -> Self:
        raise NotImplementedError


def _reg_style(register_manifest):
    # helper to format node style
    return {
        reg_name: (
            int(idxs) if isinstance(idxs, Number) else sorted(map(int, idxs)),
            str(reg_type),
        )
        for reg_name, (idxs, reg_type) in sorted(register_manifest.items())
    }
