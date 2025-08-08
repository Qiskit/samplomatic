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

"""AddNoopsActiveAccum"""

from qiskit.circuit import BoxOp, QuantumCircuit, Qubit
from qiskit.dagcircuit import DAGCircuit
from qiskit.transpiler.basepasses import TransformationPass


class AddNoopsActiveAccum(TransformationPass):
    """Expand each box to any qubits that have been marked as active so far in the circuit.

    This pass leaves non-box operations as-is, but boxes are modified to span any qubits that are
    part of a previous box.
    """

    def __init__(self):
        TransformationPass.__init__(self)

    def run(self, dag: DAGCircuit):
        # create a new dag to allow for mid-circuit modifications
        modified_dag: DAGCircuit = dag.copy_empty_like()

        # the qubits to include in the current box according to qubits covered so far
        accumulated_qubits: set[Qubit] = set()

        for node in dag.topological_op_nodes():
            if node.op.name != "box":
                modified_dag.apply_operation_back(node.op, node.qargs, node.cargs)
            else:
                content = node.op.body

                # the box should span the qubits of the original box as well as the qubits
                # that were spanned by previous boxes
                accumulated_qubits = accumulated_qubits.union(content.qubits)

                new_content = QuantumCircuit(list(accumulated_qubits), list(node.cargs))

                for op in content.data:
                    # map the qubits of each operation to their indices within all of the qubits
                    # contained in the new box
                    new_content.append(op.operation, op.qubits, op.clbits)

                box = BoxOp(new_content, annotations=node.op.annotations)
                modified_dag.apply_operation_back(box, accumulated_qubits, node.cargs)

        return modified_dag
