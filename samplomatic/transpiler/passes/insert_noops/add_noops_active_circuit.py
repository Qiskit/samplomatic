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

"""AddNoopsActiveCircuit"""

from qiskit.circuit import BoxOp
from qiskit.dagcircuit import DAGCircuit
from qiskit.transpiler.basepasses import TransformationPass

from .add_noops import AddNoops


class AddNoopsActiveCircuit(TransformationPass):
    """Expand boxes to any qubit marked as active at any point in the circuit.

    This pass leaves non-box operations as-is, but boxes are modified to span the original qubits,
    original clbits, and any qubits not already included in the original qubits which have been
    marked as active at any other point in the circuit.
    """

    def __init__(self):
        TransformationPass.__init__(self)

    def run(self, dag: DAGCircuit):
        qubits = set(qubit for box_node in dag.op_nodes(BoxOp) for qubit in box_node.qargs)
        return AddNoops(qubits).run(dag)
