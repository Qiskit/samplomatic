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

"""CollectTemplateValues"""

import numpy as np

from ...aliases import InterfaceName, ParamIndices, RegisterName, SubsystemIndices
from ...annotations import VirtualType
from ...exceptions import DeserializationError, SamplexConstructionError
from ...synths import RzRxSynth, RzSxSynth, Synth
from ...utils.serialization import array_from_json, array_to_json
from .collection_node import CollectionNode


class CollectTemplateValues(CollectionNode):
    """Collects a register slice and writes corresponding template values to output.

    Args:
        template_params_name: The name of the output to write template parameters to.
        template_idxs: An array of shape ``(num_subsystems, num_params_per_subsystem)`` specifying
            which entries of the entire template parameter value array to write to.
        register_name: The name of the register to collect.
        register_type: What kind of register type to collect.
        subsystem_idxs: The slice of the register to collect.
        synth: A synth to take the product of register values and generate template parameter
            values.

    Raises:
        SamplexConstructionError: If ``register_type`` is not compatible with ``synth``.
        SamplexConstructionError: If the second axis of ``template_idxs`` does not match
            :attr:`.Synth.num_params`, or the first axis of ``template_idxs`` does not match the
            number of subsystems in each entry of ``registers``.
    """

    def __init__(
        self,
        template_params_name: InterfaceName,
        template_idxs: ParamIndices,
        register_name: RegisterName,
        register_type: VirtualType,
        subsystem_idxs: SubsystemIndices,
        synth: Synth,
    ):
        self._template_params_name = template_params_name
        self._template_idxs = np.asarray(template_idxs, dtype=np.uint32)
        self._register_type = register_type
        self._register_name = register_name
        self._subsystem_idxs = subsystem_idxs
        self._synth = synth

        if register_type not in synth.compatible_register_types:
            raise SamplexConstructionError(
                f"{synth} is not compatible with '{register_type.value}' registers."
            )

        if self._template_idxs.ndim != 2 or self._template_idxs.shape[1] != synth.num_params:
            raise SamplexConstructionError(
                f"Argument 'template_idxs' has shape {self._template_idxs.shape}, but {synth} "
                f"expects the second axis to have size {synth.num_params}."
            )

        num_subsys = self._template_idxs.shape[0]
        self._subsystem_idxs = np.asarray(subsystem_idxs, dtype=np.uint32)
        if self._subsystem_idxs.shape != (num_subsys,):
            raise SamplexConstructionError(
                f"Expected to reference {num_subsys} subsystems of '{register_name}', but "
                f"received shape {self._subsystem_idxs.shape} instead."
            )

    def _to_json_dict(self) -> dict[str, str]:
        return {
            "node_type": "1",
            "template_param_names": self._template_params_name,
            "template_idxs": array_to_json(self._template_idxs),
            "register_type": self._register_type,
            "register_name": self._register_name,
            "subsystem_idxs": array_to_json(self._subsystem_idxs),
            "synth": type(self._synth).__name__,
        }

    @classmethod
    def _from_json_dict(cls, data: dict[str, str]) -> "CollectTemplateValues":
        synth_class_name = data["synth"]
        if synth_class_name == "RzRxSynth":
            synth = RzRxSynth()
        elif synth_class_name == "RzSxSynth":
            synth = RzSxSynth()
        else:
            raise DeserializationError(f"Invalid Synth class: {synth_class_name}")

        return cls(
            data["template_param_names"],
            array_from_json(data["template_idxs"]),
            data["register_name"],
            VirtualType(data["register_type"]),
            array_from_json(data["subsystem_idxs"]),
            synth,
        )

    @property
    def num_subsystems(self):
        """The number of subsystems being collected."""
        return self._template_idxs.shape[0]

    def outputs_to(self):
        return [self._template_params_name]

    def reads_from(self):
        return {self._register_name: (set(self._subsystem_idxs), self._register_type)}

    def validate_and_update(self, register_descriptions):
        super().validate_and_update(register_descriptions)

        _, found_type = register_descriptions[self._register_name]
        if found_type is not self._register_type:
            raise SamplexConstructionError(
                f"{self} expects {self._register_name} to be of type '{self._register_type}' "
                f"but found '{found_type}'."
            )

    def collect(self, registers, outputs, rng):
        virtual_register = registers[self._register_name][self._subsystem_idxs]

        # shape (num_subsys, num_samples, num_params_per_subsys)
        values = self._synth.generate_template_values(virtual_register).astype(np.float32)
        # shape (num_samples, total_num_params)
        all_values = outputs[self._template_params_name]
        # (num_subsys * num_params_per_subsys)
        template_idxs = self._template_idxs.ravel()

        all_values[:, template_idxs] = values.transpose(1, 0, 2).reshape(-1, template_idxs.size)

    def get_style(self):
        return (
            super()
            .get_style()
            .append_data("Output Name", repr(self._template_params_name))
            .append_data("Template Indices", self._template_idxs.tolist())
            .append_data("Register Name", repr(self._register_name))
            .append_data(Synth, repr(self._synth))
        )
