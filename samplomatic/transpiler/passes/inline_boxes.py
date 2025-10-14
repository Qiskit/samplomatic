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

"""InlineBoxes"""

from qiskit.circuit import Clbit, Qubit
from qiskit.converters import circuit_to_dag
from qiskit.dagcircuit import DAGCircuit
from qiskit.transpiler.basepasses import TransformationPass

from ...aliases import DAGOpNode


class InlineBoxes(TransformationPass):
    """Inline every box in the input circuit by replacing it with its content.

    Every annotation that is present in the boxes is ignored.
    """

    def __init__(self):
        TransformationPass.__init__(self)

    def run(self, dag: DAGCircuit) -> DAGCircuit:
        inlined_dag = dag.copy_empty_like()
        for node in dag.op_nodes():
            if node.name == "box":
                inlined_dag.compose(self._inline_box(node), list(node.qargs), list(node.cargs))
            else:
                inlined_dag.apply_operation_back(node.op, node.qargs, node.cargs)
        return inlined_dag

    def _inline_box(self, node: DAGOpNode) -> DAGCircuit:
        """Inline the content of a box with the rest of the circuit.

        It is called recursively for boxes that contain boxes.

        .. note ::
            This function assumes, but does not check, that ``node`` contains a box.

        Args:
            A node that contains a box.

        Return:
            A DAG circuit containing the operation in the box.
        """
        body = node.op.body
        qubit_map: dict[Qubit, Qubit] = dict(zip(body.qubits, node.qargs))
        clbit_map: dict[Clbit, Clbit] = dict(zip(body.clbits, node.cargs))

        content = DAGCircuit()
        content.add_qubits(node.qargs)
        content.add_clbits(node.cargs)

        for box_node in circuit_to_dag(body).topological_op_nodes():
            qargs = [qubit_map[qubit] for qubit in box_node.qargs]
            cargs = [clbit_map[clbit] for clbit in box_node.cargs]
            if box_node.op.name == "box":
                content.compose(self._inline_box(box_node), qargs, cargs)
            else:
                content.apply_operation_back(box_node.op, qargs, cargs)

        return content
