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

"""CollectZ2ToOutputNode"""

from collections.abc import Sequence

import numpy as np

from ...aliases import InterfaceName, OutputIndex, RegisterName, SubsystemIndex
from ...annotations import VirtualType
from ...exceptions import SamplexConstructionError
from .collection_node import CollectionNode


class CollectZ2ToOutputNode(CollectionNode):
    r"""Reads from :class:`~.Z2Register`\s and writes to :class:`~.SamplexOutput`.

    Args:
        register_name: The name of the register to read from.
        subsystem_idxs: The subsystems to read from.
        output_name: The name of the output to write to.
        output_idxs: The indices of the output to write to.
    """

    def __init__(
        self,
        register_name: RegisterName,
        subsystem_idxs: Sequence[SubsystemIndex],
        output_name: InterfaceName,
        output_idxs: Sequence[OutputIndex],
    ):
        self._register_name = register_name
        self._output_name = output_name
        self._subsystem_idxs = np.asarray(subsystem_idxs, dtype=np.uint32)
        self._output_idxs = np.asarray(output_idxs, dtype=np.uint32)

    def reads_from(self):
        return {self._register_name: (set(self._subsystem_idxs), VirtualType.Z2)}

    def outputs_to(self):
        return {self._output_name: (set(self._output_idxs), VirtualType.Z2)}

    def validate_and_update(self, register_descriptions):
        super().validate_and_update(register_descriptions)

        _, found_type = register_descriptions[self._register_name]
        if found_type is not VirtualType.Z2:
            raise SamplexConstructionError(
                f"{self} expects '{self._register_name}' to be of type '{found_type}'"
                f"but found '{found_type}'."
            )

    def collect(self, registers, outputs, rng):
        register = registers[self._register_name]
        output = outputs[self._output_name]
        output.reshape(-1, output.shape[-1])[:, self._output_idxs] = register.virtual_gates[
            self._subsystem_idxs, :
        ].transpose(1, 0)

    def __eq__(self, other):
        return (
            isinstance(other, CollectZ2ToOutputNode)
            and self._register_name == other._register_name
            and self._output_name == other._output_name
            and np.array_equal(self._subsystem_idxs, other._subsystem_idxs)
            and np.array_equal(self._output_idxs, other._output_idxs)
        )

    def get_style(self):
        style = (
            super()
            .get_style()
            .append_data("Register Name", repr(self._register_name))
            .append_data("Output Name", self._output_name)
            .append_data("Subsystem Indices", self._subsystem_idxs)
        )
        style.marker = "bowtie"
        style.color = "purple"
        return style
