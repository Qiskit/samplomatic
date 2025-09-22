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

"""BoxTemplateBuilder"""

from __future__ import annotations

from copy import deepcopy

import numpy as np
from qiskit.circuit import Barrier, IfElseOp, QuantumCircuit

from ...aliases import CircuitInstruction, ParamIndices
from ...exceptions import TemplateBuildError
from ...partition import QubitPartition
from ..builder import Builder
from ..specs import CollectionSpec, InstructionMode, InstructionSpec
from .template_state import TemplateState


class BoxTemplateBuilder(Builder[TemplateState, InstructionSpec]):
    """Builds dressed boxes."""

    def __init__(self, collection: CollectionSpec):
        super().__init__()

        self.collection = collection
        self.measured_qubits = set()
        self.entangled_qubits = set()
        self.already_collected_qubits = set()

    def _append_dressed_layer(
        self, target_circuit: QuantumCircuit | None = None, qubits: QubitPartition | None = None
    ) -> ParamIndices:
        """Add a collection dressing layer.

        Args:
            target_circuit: The `QuantumCircuit` to which the dressing is added. Defaults to the
                template.
            qubits: The qubits to be collected. Defaults to the qubits of the `CollectionSpec`.
        """
        qubits = qubits if qubits is not None else self.collection.qubits
        if target_circuit is None:
            target_circuit = self.state.template
            try:
                remapped_qubits = [
                    list(map(lambda k: self.state.qubit_map[k], subsys)) for subsys in qubits
                ]
            except KeyError:
                not_found = {
                    qubit
                    for subsys in qubits
                    for qubit in subsys
                    if qubit not in self.state.qubit_map
                }
                raise TemplateBuildError(
                    f"The qubits '{not_found}' could not be found when recursing into a box of the "
                    "input circuit."
                ) from KeyError
        else:
            remapped_qubits = qubits

        param_idx_start = self.state.param_iter.idx
        num_params = len(qubits) * self.collection.synth.num_params
        param_idxs = np.arange(param_idx_start, param_idx_start + num_params, dtype=np.intp)

        for subsys_remapped_qubits in remapped_qubits:
            for instr in self.collection.synth.make_template(
                subsys_remapped_qubits, self.state.param_iter
            ):
                target_circuit.append(instr)

        return param_idxs.reshape(len(qubits), -1)

    def _append_barrier(self, label: str):
        label = f"{label}{'_'.join(map(str, self.state.scope_idx))}"
        all_qubits = self.state.qubit_map.values()
        barrier = CircuitInstruction(Barrier(len(all_qubits), label), all_qubits)
        self.state.template.append(barrier)

    def _remap_subcircuit(
        self, sub_circuit: QuantumCircuit, target_circuit: QuantumCircuit | None = None
    ) -> tuple[QuantumCircuit, list[InstructionSpec]]:
        """Remap a subcircuit."""
        # TODO: TemplateState has a similar function. Are both needed?
        if target_circuit is None:
            target_circuit = QuantumCircuit(sub_circuit.qubits, sub_circuit.clbits)
        specs = [self.parse(instr, target_circuit) for instr in sub_circuit]

        return (target_circuit, specs)


class LeftBoxTemplateBuilder(BoxTemplateBuilder):
    """Box builder for left dressings."""

    def __init__(self, collection: CollectionSpec):
        super().__init__(collection=collection)

        self.qubits_in_conditionals = set()

    def set_state(self, state):
        self._box_circuit = state.template.copy_empty_like(vars_mode="captures")
        return super().set_state(state)

    def parse(
        self, instr: CircuitInstruction, target_circuit: QuantumCircuit | None = None
    ) -> InstructionSpec:
        if target_circuit is None:
            target_circuit = self._box_circuit

        if (name := instr.operation.name).startswith("if_else"):
            # We need to remap both branches and add collectors to both of them.

            # The same entangled_qubits should be used for both branches, so we copy.
            original_entangled_qubits = deepcopy(self.entangled_qubits)

            # All of the qubits in the conditional will be collected here.
            # It's important to do this first as there are nested call to parse.
            self.already_collected_qubits.update(instr.qubits)

            true_body = QuantumCircuit(
                instr.operation.params[0].qubits, instr.operation.params[0].clbits
            )
            if instr.operation.params[1] is not None:
                false_body = QuantumCircuit(
                    instr.operation.params[1].qubits, instr.operation.params[1].clbits
                )
            else:
                # TODO: Can we just assume that both branches have the same bits?
                false_body = QuantumCircuit(
                    instr.operation.params[0].qubits, instr.operation.params[0].clbits
                )

            true_param_idxs = self._append_dressed_layer(
                true_body, QubitPartition.from_elements(instr.qubits)
            )
            false_param_idxs = self._append_dressed_layer(
                false_body, QubitPartition.from_elements(instr.qubits)
            )

            true_body, true_specs = self._remap_subcircuit(instr.operation.params[0], true_body)
            temp_entangled_qubits = self.entangled_qubits
            self.entangled_qubits = original_entangled_qubits

            false_body, false_specs = (
                self._remap_subcircuit(instr.operation.params[1], false_body)
                if instr.operation.params[1] is not None
                else (false_body, [])
            )
            self.entangled_qubits.update(temp_entangled_qubits)
            ifelse_op = IfElseOp(
                condition=instr.operation.condition,
                true_body=true_body,
                false_body=false_body,
                label=instr.operation.label,
            )
            self.state.template.append(CircuitInstruction(ifelse_op, instr.qubits, instr.clbits))

            return InstructionSpec(
                if_else=(true_specs, true_param_idxs, false_specs, false_param_idxs),
                clbit_idxs=self.state.get_condition_clbits(instr.operation.condition),
            )

        if to_be_collected := [
            qubit for qubit in instr.qubits if qubit not in self.already_collected_qubits
        ]:
            param_idxs = self._append_dressed_layer(
                qubits=QubitPartition.from_elements(to_be_collected)
            )
            self.already_collected_qubits.update(to_be_collected)
        else:
            param_idxs = np.empty((0, 0), dtype=np.intp)

        if name == "barrier":
            return InstructionSpec(
                params=self.state.append_remapped_gate(instr, target_circuit),
                param_idxs=param_idxs,
            )

        elif name.startswith("meas"):
            self.measured_qubits.update(instr.qubits)
            return InstructionSpec(
                params=self.state.append_remapped_gate(instr, target_circuit),
                clbit_idxs=[self.state.template.find_bit(clbit)[0] for clbit in instr.clbits],
                param_idxs=param_idxs,
            )

        elif (num_qubits := instr.operation.num_qubits) == 1:
            if not self.measured_qubits.isdisjoint(instr.qubits):
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
            return InstructionSpec(
                params=params, mode=InstructionMode.MULTIPLY, param_idxs=param_idxs
            )

        elif num_qubits > 1:
            self.entangled_qubits.update(instr.qubits)
            return InstructionSpec(
                params=self.state.append_remapped_gate(instr, target_circuit),
                mode=InstructionMode.PROPAGATE,
                param_idxs=param_idxs,
            )
        raise RuntimeError(f"Instruction {instr} could not be parsed.")

    def lhs(self) -> InstructionSpec:
        self._append_barrier("L")

    def rhs(self) -> InstructionSpec:
        if remaining_qubits := self.collection.qubits.difference(self.already_collected_qubits):
            param_idxs = self._append_dressed_layer(qubits=remaining_qubits)
        else:
            param_idxs = np.empty((0, 0), dtype=np.intp)
        self._append_barrier("M")
        self.state.template.compose(
            self._box_circuit, inplace=True, copy=False, inline_captures=True
        )
        self._append_barrier("R")
        return InstructionSpec(param_idxs=param_idxs)


class RightBoxTemplateBuilder(BoxTemplateBuilder):
    """Box builder for right dressings."""

    def parse(
        self, instr: CircuitInstruction, target_circuit: QuantumCircuit | None = None
    ) -> InstructionSpec:
        if (name := instr.operation.name) == "barrier":
            return InstructionSpec(params=self.state.append_remapped_gate(instr))

        if not self.already_collected_qubits.isdisjoint(instr.qubits):
            raise RuntimeError("Cannot handle instructions to the right of if-else ops.")

        elif name.startswith("meas"):
            raise RuntimeError("Boxes with measurements cannot have dressing=right.")

        elif name.startswith("if_else"):
            # We need to remap both branches and add collectors to both of them.

            # The same entangled_qubits should be used for both branches, so we copy.
            # Because there are no measurements in right-dressed boxes, it's the only property
            # we need to copy.
            original_entangled_qubits = deepcopy(self.entangled_qubits)
            true_body, true_specs = self._remap_subcircuit(instr.operation.params[0])
            temp_entangled_qubits = self.entangled_qubits
            self.entangled_qubits = original_entangled_qubits

            false_body, false_specs = (
                self._remap_subcircuit(instr.operation.params[1])
                if instr.operation.params[1] is not None
                else (instr.operation.params[0].copy_empty_like(), [])
            )
            self.entangled_qubits.update(temp_entangled_qubits)

            true_param_idxs = self._append_dressed_layer(
                true_body, QubitPartition.from_elements(instr.qubits)
            )
            false_param_idxs = self._append_dressed_layer(
                false_body, QubitPartition.from_elements(instr.qubits)
            )

            ifelse_op = IfElseOp(
                condition=instr.operation.condition,
                true_body=true_body,
                false_body=false_body,
                label=instr.operation.label,
            )
            self.state.template.append(CircuitInstruction(ifelse_op, instr.qubits, instr.clbits))

            self.already_collected_qubits.update(instr.qubits)

            return InstructionSpec(
                if_else=(true_specs, true_param_idxs, false_specs, false_param_idxs),
                clbit_idxs=self.state.get_condition_clbits(instr.operation.condition),
            )

        elif (num_qubits := instr.operation.num_qubits) == 1:
            self.entangled_qubits.update(instr.qubits)
            # the action of this single-qubit gate will be absorbed into the dressing
            params = []
            if instr.operation.is_parameterized():
                params.extend((None, param) for param in instr.operation.params)
            return InstructionSpec(mode=InstructionMode.MULTIPLY, params=params)

        elif num_qubits > 1:
            if not self.entangled_qubits.isdisjoint(instr.qubits):
                raise RuntimeError(
                    "Cannot handle single-qubit gate to the left of entangler when dressing=right."
                )
            return InstructionSpec(
                params=self.state.append_remapped_gate(instr, target_circuit),
                mode=InstructionMode.PROPAGATE,
            )

        raise RuntimeError(f"Instruction {instr} could not be parsed.")

    def lhs(self) -> InstructionSpec:
        self._append_barrier("L")
        return InstructionSpec()

    def rhs(self) -> InstructionSpec:
        self._append_barrier("M")
        if len(to_collect := self.collection.qubits.difference(self.already_collected_qubits)) > 0:
            param_idxs = self._append_dressed_layer(qubits=to_collect)
        else:
            param_idxs = None
        self._append_barrier("R")
        return InstructionSpec(param_idxs=param_idxs)
