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

from __future__ import annotations

from qiskit.circuit import ClassicalRegister, Clbit, QuantumCircuit, QuantumRegister, Qubit
from qiskit.circuit.classical import expr

from ...aliases import CircuitInstruction, ClbitIndex, ParamSpec, QubitIndex, Self
from ...exceptions import TemplateBuildError
from ..param_iter import ParamIter


class TemplateState:
    """The state of a template construction owned by a template builder.

    Args:
        template: The template quantum circuit being built.
        qubit_map: A map from qubits in the source circuit to corresponding qubits in the template.
        param_iter: An iterator over parameters to use in the circuit being built.
        scope_idx: The nested index of the scope currently being built.
    """

    def __init__(
        self,
        template: QuantumCircuit,
        qubit_map: dict[Qubit, QubitIndex],
        param_iter: ParamIter,
        scope_idx: list[int],
    ):
        self.template: QuantumCircuit = template
        self.qubit_map = qubit_map
        self.param_iter = param_iter
        self.scope_idx = scope_idx

    def remap(
        self, scoped_qubit_map: dict[QubitIndex, Qubit], last_scope_idx: int | None = None
    ) -> TemplateState:
        """Return a new :class:`~.TemplateState` whose source qubits are different.

        Args:
            scoped_qubit_map: A map to qubits in some inner scope from qubits in its parent scope.
            last_scope_idx: A new nesting level to append to the scope index, if wanted.

        Returns:
            A new :class:`~.TemplateState` pointing to the same template and param iter, but where
            the qubit map has a new source.
        """
        new_qubit_map = {
            qubit: self.qubit_map[parent_scope_qubit]
            for qubit, parent_scope_qubit in scoped_qubit_map.items()
        }
        scope_idx = self.scope_idx if last_scope_idx is None else self.scope_idx + [last_scope_idx]
        return TemplateState(self.template, new_qubit_map, self.param_iter, scope_idx)

    @classmethod
    def construct_for_circuit(cls, circuit: QuantumCircuit) -> Self:
        """Construct a new instance from a quantum circuit.

        Use this method when you need a to parse the entirety of a particular circuit.

        Args:
            circuit: The circuit you intend to parse.
        """
        template_circuit = QuantumCircuit(QuantumRegister(circuit.num_qubits, "q"), *circuit.cregs)
        qubit_map = {q: idx for idx, q in enumerate(circuit.qubits)}

        # quick and dirty heuristic to get the max params roughly correct with a safety factor
        # TODO: This estimate might not hold for dynamic circuits, where the same qubit will be
        # collected twice - once in the if branch and another in the else branch.
        max_params = 3 * sum(
            len(instr.qubits) for instr in circuit if instr.operation.name == "box"
        )
        max_params += circuit.num_parameters
        param_iter = ParamIter(5 * max_params)

        return cls(template_circuit, qubit_map, param_iter, [])

    def append_remapped_gate(
        self, instr: CircuitInstruction, target_circuit: QuantumCircuit | None = None
    ) -> ParamSpec:
        """Remap the parameters and qubits of an instruction gate and append it to the circuit."""
        if target_circuit is None:
            target_circuit = self.template

        new_params = []
        param_mapping = []
        for param in instr.operation.params:
            param_mapping.append([self.param_iter.idx, param])
            new_params.append(next(self.param_iter))

        new_qubits = [self.qubit_map.get(qubit, qubit) for qubit in instr.qubits]
        new_operation = type(instr.operation)(*new_params) if new_params else instr.operation
        target_circuit.append(CircuitInstruction(new_operation, new_qubits, instr.clbits))

        return param_mapping

    def remap_subcircuit(self, circuit: QuantumCircuit) -> tuple[QuantumCircuit, ParamSpec]:
        """Remap the parameters and qubits of a sub-circuit."""
        new_qubits = [
            self.template.qubits[self.qubit_map[qubit]] if qubit in self.qubit_map else qubit
            for qubit in circuit.qubits
        ]
        remapped_circuit = QuantumCircuit(new_qubits, circuit.clbits)
        param_mapping = []

        for instr in circuit:
            new_qubits = [
                self.template.qubits[self.qubit_map[qubit]] if qubit in self.qubit_map else qubit
                for qubit in instr.qubits
            ]
            new_params = []
            instr_param_mapping = []
            for param in instr.operation.params:
                instr_param_mapping.append([self.param_iter.idx, param])
                new_params.append(next(self.param_iter))

            new_operation = type(instr.operation)(*new_params) if new_params else instr.operation
            remapped_circuit.append(CircuitInstruction(new_operation, new_qubits, instr.clbits))
            param_mapping.extend(instr_param_mapping)

        return (remapped_circuit, param_mapping)

    def get_condition_clbits(
        self, condition: tuple[ClassicalRegister, int] | tuple[Clbit, int] | expr.Expr
    ) -> list[ClbitIndex]:
        """Return the indices of the classical bits involved in an `IfElseOp` condition.

        Args:
            condition: The condition to be evaluated.

        Raises:
            TemplateBuildError: If the condition is of unknown form.
        """
        if isinstance(condition, expr.Expr):
            clbits = []
            for var in expr.iter_vars(condition):
                if isinstance(var.var, Clbit):
                    clbits.append(self.template.find_bit(var.var).index)
                if isinstance(var.var, ClassicalRegister):
                    clbits.extend(self.template.find_bit(clbit).index for clbit in var.var)
            return clbits
        elif isinstance(condition[0], ClassicalRegister):
            return [self.template.find_bit(clbit).index for clbit in condition[0]]
        elif isinstance(condition[0], Clbit):
            return [self.template.find_bit(condition[0]).index]
        else:
            raise TemplateBuildError(
                "A classical condition should be a 2-tuple of `(ClassicalRegister | Clbit, int)`,"
                f" or a classical `Expr` but received '{condition}'."
            )
