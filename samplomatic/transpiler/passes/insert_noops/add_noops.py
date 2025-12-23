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

"""AddNoops"""

from collections.abc import Iterable

from qiskit.circuit import BoxOp, QuantumCircuit, Qubit
from qiskit.dagcircuit import DAGCircuit, DAGInNode, DAGNode, DAGOpNode
from qiskit.transpiler.basepasses import TransformationPass
from qiskit.transpiler.exceptions import TranspilerError


def extend_boxes(dag: DAGCircuit, qubits: set[Qubit]) -> DAGCircuit:
    new_dag: DAGCircuit = dag.copy_empty_like()

    # all nodes that have been added to new_dag so far
    added_nodes: set[DAGNode] = set()

    # all nodes visited, in topological order
    all_visited_nodes: list[DAGOpNode] = []

    for node in dag.topological_op_nodes():
        if node.op.name == "box":
            backwards_lightcone = []

            for ancestor_node in dag.ancestors(node):
                if ancestor_node not in added_nodes:
                    backwards_lightcone.append(ancestor_node)

            for unapplied_node in reversed(backwards_lightcone[1:]):
                if not isinstance(unapplied_node, DAGInNode):
                    new_dag.apply_operation_back(unapplied_node)
                added_nodes.add(unapplied_node)

            box_qubits = qubits.union(node.qargs)
            box_qubits = [qubit for qubit in dag.qubits if qubit in box_qubits]
            qubit_map = dict(zip(node.op.body.qubits, node.qargs)).get
            new_box_body = QuantumCircuit(box_qubits, list(node.op.body.clbits))
            for instr in node.op.body:
                new_box_body.append(
                    instr.operation, list(map(qubit_map, instr.qubits)), instr.clbits
                )
            new_box = BoxOp(new_box_body, annotations=node.op.annotations)
            new_dag.apply_operation_back(new_box, box_qubits, node.cargs)
            added_nodes.add(node)
        else:
            all_visited_nodes.append(node)

    # add all those nodes we haven't had the pleasure of yet adding
    for node in all_visited_nodes:
        if node not in added_nodes:
            new_dag.apply_operation_back(node.op, node.qargs, node.cargs)

    return new_dag


class AddNoops(TransformationPass):
    """Expand boxes to the given ``qubits``.

    This pass leaves non-box operations as-is, but boxes are modified to span the original qubits,
    original clbits, and any user-specified qubits not already included in the original qubits.

    Args:
        qubits: The qubits to which to extend all boxes.
    """

    def __init__(self, qubits: Iterable[int] | Iterable[Qubit]):
        super().__init__()

        self._qubits_are_ints = all(isinstance(qubit, int) for qubit in qubits)
        if not (self._qubits_are_ints or all(isinstance(qubit, Qubit) for qubit in qubits)):
            raise TranspilerError(
                "Invalid type used for specifying qubits. Expected ``Qubit``s or "
                "``int``s, but found both."
            )
        self.qubits = set(qubits)

    def run(self, dag: DAGCircuit):
        # safety check for type of self.qubits
        if not self.qubits:
            return dag

        if self._qubits_are_ints:
            if max(self.qubits) > dag.num_qubits() - 1:
                raise TranspilerError("Not all of the specified qubits are in this circuit.")
            qubits = {dag.qubits[idx] for idx in self.qubits}
        else:
            if any(qubit not in dag.qubits for qubit in self.qubits):
                raise TranspilerError("Not all of the specified qubits are in this circuit.")
            qubits = self.qubits

        return extend_boxes(dag.reverse_ops(), qubits).reverse_ops()
