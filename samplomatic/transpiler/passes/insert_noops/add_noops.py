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

from __future__ import annotations

from collections.abc import Iterable

from qiskit.circuit import BoxOp, QuantumCircuit, Qubit
from qiskit.dagcircuit import DAGCircuit
from qiskit.transpiler.basepasses import TransformationPass
from qiskit.transpiler.exceptions import TranspilerError


class AddNoops(TransformationPass):
    """Expand boxes to the given ``qubits``.

    This pass leaves non-box operations as-is, but boxes are modified to span the original qubits,
    original clbits, and any user-specified qubits not already included in the original qubits.
    """

    def __init__(self, qubits: Iterable[int] | Iterable[Qubit]):
        TransformationPass.__init__(self)
        if not (
            all(isinstance(qubit, int) for qubit in qubits)
            or all(isinstance(qubit, Qubit) for qubit in qubits)
        ):
            raise TranspilerError(
                "Invalid type used for specifying qubits. Expected ``Qubit``s or "
                "``int``s, but found both."
            )
        self.qubits = set(qubits)

    def run(self, dag: DAGCircuit):
        # create a new dag to allow for mid-circuit modifications
        new_dag: DAGCircuit = dag.copy_empty_like()

        # safety check for type of self.qubits
        if not self.qubits:
            return dag

        if all(isinstance(qubit, int) for qubit in self.qubits):
            if max(self.qubits) > dag.num_qubits() - 1:
                raise TranspilerError("Not all of the specified qubits are in this circuit.")
            qubits = {dag.qubits[idx] for idx in self.qubits}
        else:
            if any(qubit not in dag.qubits for qubit in self.qubits):
                raise TranspilerError("Not all of the specified qubits are in this circuit.")
            qubits = self.qubits

        for node in dag.topological_op_nodes():
            if node.op.name != "box":
                new_dag.apply_operation_back(node.op, node.qargs, node.cargs)
            else:
                content = node.op.body

                # the box should span the qubits of the original box as well as the qubits
                # specified by the user
                new_qubits = qubits.union(content.qubits)
                new_content = QuantumCircuit(list(new_qubits), list(node.cargs))

                for op in content.data:
                    # map the qubits of each operation to their indices within all of the qubits
                    # contained in the new box
                    new_content.append(op.operation, op.qubits, op.clbits)

                box = BoxOp(new_content, annotations=node.op.annotations)
                new_dag.apply_operation_back(box, new_qubits, node.cargs)

        return new_dag
