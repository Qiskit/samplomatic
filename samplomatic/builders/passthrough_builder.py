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

from ..aliases import CircuitInstruction
from ..pre_samplex import PreSamplex
from .builder import Builder
from .specs import InstructionMode
from .template_state import TemplateState


class PassthroughBuilder(Builder[TemplateState, PreSamplex]):
    """Builder that passes all instructions through."""

    def parse(self, instr: CircuitInstruction):
        """Parse a single non-box instruction.

        Args:
            instr: The instruction to parse.
        """
        if instr.operation.name.startswith("if_else"):
            true_body, true_params = self.template_state.remap_subcircuit(instr.operation.params[0])
            false_body, false_params = (
                self.template_state.remap_subcircuit(instr.operation.params[1])
                if instr.operation.params[1] is not None
                else (None, [])
            )
            ifelse_op = IfElseOp(
                condition=instr.operation.condition,
                true_body=true_body,
                false_body=false_body,
                label=instr.operation.label,
            )
            qubits = [self.template_state.qubit_map[qubit] for qubit in instr.qubits]
            self.template_state.template.append(CircuitInstruction(ifelse_op, qubits, instr.clbits))

            self.samplex_state.enforce_no_propagation(instr)
            self.samplex_state.verify_no_twirled_clbits(
                self.template_state.get_condition_clbits(instr.operation.condition)
            )
            self.samplex_state.passthrough_params.extend(true_params + false_params)
        else:
            mode = InstructionMode.PROPAGATE
            params = self.template_state.append_remapped_gate(instr)
            self.samplex_state.add_propagate(instr, mode, params)

    def _append_barrier(self, label: str):
        if self.template_state.scope_idx:
            label = f"{label}{'_'.join(map(str, self.template_state.scope_idx))}"
            all_qubits = self.template_state.qubit_map.values()
            barrier = CircuitInstruction(Barrier(len(all_qubits), label), all_qubits)
            self.template_state.template.append(barrier)

    def lhs(self):
        self._append_barrier("L")

    def rhs(self):
        self._append_barrier("R")
