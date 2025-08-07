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

"""AddNoopsAll"""

from qiskit.dagcircuit import DAGCircuit
from qiskit.transpiler.basepasses import TransformationPass

from .add_noops import AddNoops


class AddNoopsAll(TransformationPass):
    """Expand boxes to all qubits contained in a circuit.

    This pass leaves non-box operations as-is, but boxes are modified to span all the qubits as
    defined when initializing the `QuantumCircuit` object.
    """

    def __init__(self):
        TransformationPass.__init__(self)

    def run(self, dag: DAGCircuit):
        return AddNoops(dag.qubits).run(dag)
