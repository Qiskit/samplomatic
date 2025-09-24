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

"""BoxBuilder"""

from __future__ import annotations

import numpy as np
from qiskit.circuit import Barrier

from ..aliases import CircuitInstruction, ParamIndices
from ..exceptions import SamplexBuildError, TemplateBuildError
from ..partition import QubitPartition
from ..pre_samplex import PreSamplex
from .builder import Builder
from .dynamic_builder import BoxLeftIfElseBuilder, BoxRightIfElseBuilder
from .specs import CollectionSpec, EmissionSpec, InstructionMode, InstructionSpec, VirtualType
from .template_state import TemplateState


class BoxBuilder(Builder[TemplateState, PreSamplex]):
    """Builds dressed boxes."""

    def __init__(self, collection: CollectionSpec, emission: EmissionSpec):
        super().__init__()

        self.collection = collection
        self.emission = emission
        self.measured_qubits = QubitPartition(1, [])
        self.entangled_qubits = set()

    def _append_dressed_layer(self) -> ParamIndices:
        """A helper function to add a collection dressing layer."""
        qubits = self.collection.qubits
        try:
            remapped_qubits = [
                list(map(lambda k: self.template_state.qubit_map[k], subsys)) for subsys in qubits
            ]
        except KeyError:
            not_found = {
                qubit
                for subsys in qubits
                for qubit in subsys
                if qubit not in self.template_state.qubit_map
            }
            raise TemplateBuildError(
                f"The qubits '{not_found}' could not be found when recursing into a box of the "
                "input circuit."
            ) from KeyError

        param_idx_start = self.template_state.param_iter.idx
        num_params = len(qubits) * self.collection.synth.num_params
        param_idxs = np.arange(param_idx_start, param_idx_start + num_params, dtype=np.intp)

        for subsys_remapped_qubits in remapped_qubits:
            for instr in self.collection.synth.make_template(
                subsys_remapped_qubits, self.template_state.param_iter
            ):
                self.template_state.template.append(instr)

        return param_idxs.reshape(len(qubits), -1)

    def _append_barrier(self, label: str):
        label = f"{label}{'_'.join(map(str, self.template_state.scope_idx))}"
        all_qubits = self.template_state.qubit_map.values()
        barrier = CircuitInstruction(Barrier(len(all_qubits), label), all_qubits)
        self.template_state.template.append(barrier)


class LeftBoxBuilder(BoxBuilder):
    """Box builder for left dressings."""

    def __init__(self, collection: CollectionSpec, emission: EmissionSpec):
        super().__init__(collection=collection, emission=emission)

        self.measured_qubits = QubitPartition(1, [])
        self.clbit_idxs = []

    def parse(self, instr: CircuitInstruction):
        name = instr.operation.name
        param_idxs = np.empty((0, 0), dtype=np.intp)

        if (name := instr.operation.name) == "barrier":
            self.template_state.append_remapped_gate(instr)
            return

        if name.startswith("meas"):
            for qubit in instr.qubits:
                if (qubit,) not in self.measured_qubits:
                    self.measured_qubits.add((qubit,))
                else:
                    raise SamplexBuildError(
                        "Cannot measure the same qubit twice in a twirling box."
                    )
            self.template_state.append_remapped_gate(instr)
            self.clbit_idxs.extend(
                [self.template_state.template.find_bit(clbit)[0] for clbit in instr.clbits]
            )
            return

        if name.startswith("if_else"):
            builder = BoxLeftIfElseBuilder(
                instr, self.samplex_state, self.collection.synth, self.template_state.param_iter
            )
            if_else = builder.build()
            new_qubits = [self.template_state.qubit_map.get(qubit, qubit) for qubit in instr.qubits]
            self.template_state.template.append(if_else, new_qubits, instr.clbits)
            return

        if (num_qubits := instr.operation.num_qubits) == 1:
            if self.measured_qubits.overlaps_with(instr.qubits):
                raise RuntimeError(
                    "Cannot handle single-qubit gate to the right of measurements when "
                    "dressing=left."
                )
            if not self.entangled_qubits.isdisjoint(instr.qubits):
                raise RuntimeError(
                    "Cannot handle single-qubit gate to the right of entangler when dressing=left."
                )
            # the action of this single-qubit gate will be absorbed into the dressing
            params = []
            if instr.operation.is_parameterized():
                params.extend((None, param) for param in instr.operation.params)
            spec = InstructionSpec(
                params=params, mode=InstructionMode.MULTIPLY, param_idxs=param_idxs
            )

        elif num_qubits > 1:
            self.entangled_qubits.update(instr.qubits)
            spec = InstructionSpec(
                params=self.template_state.append_remapped_gate(instr),
                mode=InstructionMode.PROPAGATE,
                param_idxs=param_idxs,
            )
        else:
            raise RuntimeError(f"Instruction {instr} could not be parsed.")

        if self.measured_qubits.overlaps_with(instr.qubits):
            # TODO: What about delays? barriers?
            raise SamplexBuildError(
                f"Instruction {instr} happens after a measurement. No operations allowed "
                "after a measurement in a measurement twirling box."
            )
        self.samplex_state.add_propagate(instr, spec)

    def lhs(self):
        self._append_barrier("L")
        param_idxs = self._append_dressed_layer()
        self.samplex_state.add_collect(self.collection.qubits, self.collection.synth, param_idxs)
        self._append_barrier("M")

    def rhs(self):
        self._append_barrier("R")

        if self.emission.noise_ref:
            self.samplex_state.add_emit_noise_left(
                self.emission.qubits, self.emission.noise_ref, self.emission.noise_modifier_ref
            )
        if self.emission.basis_ref:
            self.samplex_state.add_emit_meas_basis_transform(
                self.emission.qubits, self.emission.basis_ref
            )
        if twirl_type := self.emission.twirl_register_type:
            self.samplex_state.add_emit_twirl(self.emission.qubits, twirl_type)
            if len(self.measured_qubits) != 0:
                if twirl_type != VirtualType.PAULI:
                    raise SamplexBuildError(
                        f"Cannot use {twirl_type.value} twirl in a box with measurements."
                    )
                self.samplex_state.add_z2_collect(self.measured_qubits, self.clbit_idxs)


class RightBoxBuilder(BoxBuilder):
    """Box builder for right dressings."""

    def parse(self, instr: CircuitInstruction):
        if (name := instr.operation.name).startswith("meas"):
            raise RuntimeError("Boxes with measurements cannot have dressing=right.")

        if name == "barrier":
            spec = InstructionSpec(params=self.template_state.append_remapped_gate(instr))
            return

        if name.startswith("if_else"):
            builder = BoxRightIfElseBuilder(
                instr, self.samplex_state, self.collection.synth, self.template_state.param_iter
            )
            if_else = builder.build()
            new_qubits = [self.template_state.qubit_map.get(qubit, qubit) for qubit in instr.qubits]
            self.template_state.template.append(if_else, new_qubits, instr.clbits)
            return

        if (num_qubits := instr.operation.num_qubits) == 1:
            self.entangled_qubits.update(instr.qubits)
            # the action of this single-qubit gate will be absorbed into the dressing
            params = []
            if instr.operation.is_parameterized():
                params.extend((None, param) for param in instr.operation.params)
            spec = InstructionSpec(mode=InstructionMode.MULTIPLY, params=params)

        elif num_qubits > 1:
            if not self.entangled_qubits.isdisjoint(instr.qubits):
                raise RuntimeError(
                    "Cannot handle single-qubit gate to the left of entangler when dressing=right."
                )
            spec = InstructionSpec(
                params=self.template_state.append_remapped_gate(instr),
                mode=InstructionMode.PROPAGATE,
            )
        else:
            raise RuntimeError(f"Instruction {instr} could not be parsed.")

        self.samplex_state.add_propagate(instr, spec)

    def lhs(self):
        self._append_barrier("L")

        if self.emission.basis_ref:
            self.samplex_state.add_emit_prep_basis_transform(
                self.emission.qubits, self.emission.basis_ref
            )
        if self.emission.noise_ref:
            self.samplex_state.add_emit_noise_right(
                self.emission.qubits, self.emission.noise_ref, self.emission.noise_modifier_ref
            )
        if self.emission.twirl_register_type:
            self.samplex_state.add_emit_twirl(
                self.emission.qubits, self.emission.twirl_register_type
            )

    def rhs(self):
        self._append_barrier("M")
        param_idxs = self._append_dressed_layer()
        self.samplex_state.add_collect(self.collection.qubits, self.collection.synth, param_idxs)
        self._append_barrier("R")
