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

"""RemoveBoxes"""

from qiskit.circuit import Clbit, Qubit
from qiskit.converters import circuit_to_dag
from qiskit.dagcircuit import DAGCircuit
from qiskit.transpiler.basepasses import TransformationPass


class RemoveBoxes(TransformationPass):
    """Return a circuit with any boxes removed."""

    def __init__(self):
        TransformationPass.__init__(self)

    def run(self, dag: DAGCircuit) -> DAGCircuit:
        new_dag = dag.copy_empty_like()

        for node in dag.op_nodes():
            if node.op.name == "box":
                self._inline_box(dag, node)
            else:
                new_dag.apply_operation_back(node.op, node.qargs, node.cargs)

        return new_dag

    def _inline_box(self, dag, node) -> DAGCircuit:
        body = node.op.body
        qubit_map: dict[Qubit, Qubit] = dict(zip(body.qubits, node.qargs))
        clbit_map: dict[Clbit, Clbit] = dict(zip(body.clbits, node.cargs))

        for body_node in circuit_to_dag(body).topological_op_nodes():
            if body_node.op.name == "box":
                self._inline_box(dag, body_node)
            else:
                qargs = [qubit_map[qubit] for qubit in body_node.qargs]
                cargs = [clbit_map[clbit] for clbit in body_node.cargs]
                dag.apply_operation_back(body_node.op, qargs, cargs)

        return dag
