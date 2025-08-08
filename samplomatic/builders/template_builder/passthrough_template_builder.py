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

"""TemplateCircuitBuilder"""

from qiskit.circuit import Barrier, IfElseOp

from ...aliases import CircuitInstruction
from ..builder import Builder
from ..specs import InstructionMode, InstructionSpec
from .template_state import TemplateState


class PassthroughTemplateBuilder(Builder[TemplateState, InstructionSpec]):
    """Template builder that passes all instructions through."""

    def parse(self, instr: CircuitInstruction) -> InstructionSpec:
        """Parse a single non-box instruction.

        Args:
            instr: The instruction to parse.

        Returns:
            An `InstructionSpec` with a map from where new parameters are located to how to
            evaluate their values when the time comes.
        """
        if instr.operation.name.startswith("if_else"):
            true_body, true_params = self.state.remap_subcircuit(instr.operation.params[0])
            false_body, false_params = (
                self.state.remap_subcircuit(instr.operation.params[1])
                if instr.operation.params[1] is not None
                else (None, [])
            )
            ifelse_op = IfElseOp(
                condition=instr.operation.condition,
                true_body=true_body,
                false_body=false_body,
                label=instr.operation.label,
            )
            qubits = [self.state.qubit_map[qubit] for qubit in instr.qubits]
            self.state.template.append(CircuitInstruction(ifelse_op, qubits, instr.clbits))
            return InstructionSpec(
                params=true_params + false_params,
                clbit_idxs=self.state.get_condition_clbits(instr.operation.condition),
            )
        else:
            return InstructionSpec(
                params=self.state.append_remapped_gate(instr), mode=InstructionMode.PROPAGATE
            )

    def _append_barrier(self, label: str):
        if self.state.scope_idx:
            label = f"{label}{'_'.join(map(str, self.state.scope_idx))}"
            all_qubits = self.state.qubit_map.values()
            barrier = CircuitInstruction(Barrier(len(all_qubits), label), all_qubits)
            self.state.template.append(barrier)

    def lhs(self) -> InstructionSpec:
        self._append_barrier("L")
        return InstructionSpec()

    def rhs(self) -> InstructionSpec:
        self._append_barrier("R")
        return InstructionSpec()
