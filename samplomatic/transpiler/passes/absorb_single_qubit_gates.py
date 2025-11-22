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

"""AbsorbSingleQubitGates"""

from __future__ import annotations

from collections import defaultdict

from qiskit.circuit import BoxOp, Qubit
from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit.dagcircuit import DAGCircuit
from qiskit.transpiler.basepasses import TransformationPass

from ...aliases import DAGOpNode
from ...constants import STANDARD_1Q_GATES


class AbsorbSingleQubitGates(TransformationPass):
    """Absorb all chains of single-qubit gates that are left of a box instruction into the box.

    Any instruction that is not a single-qubit gate, including measurements, entanglers, barriers,
    and boxes, is considerred an interruption, and ends a chain. For example, if an X, a
    measurement, a Y, and a Z gate precede a box in this order, then the Y and the Z will be
    absorbed into the box, but the X and the measurement will not.
    """

    def run(self, dag: DAGCircuit) -> DAGCircuit:
        """Perform rightwards absorption of chains of single-qubit gates."""
        # A map from box op nodes to predecessor runs of single-qubit gates
        single_qubit_runs: dict[DAGOpNode, dict[Qubit, tuple[DAGOpNode]]] = defaultdict(dict)

        # first, we collect the runs but don't move anything
        for single_qubit_run in dag.collect_runs(list(STANDARD_1Q_GATES)):
            # the run will always have at least one element, and they are in circuit order
            last_gate = single_qubit_run[-1]
            # this loop should have 0 or 1 iteration because the run is on a single qubit
            for successor in dag.quantum_successors(last_gate):
                # at the end of a circuit, successor is not a DAGOpNode and has no 'op' attribute
                if isinstance(successor, DAGOpNode) and successor.op.name == "box":
                    qubit = last_gate.qargs[0]
                    single_qubit_runs[successor][qubit] = single_qubit_run

        # now we can loop through unique boxes and deal with them one at a time
        for box_node, per_qubit_runs in single_qubit_runs.items():
            # we convert to a dag to make it easier to add on the lhs
            box_dag = circuit_to_dag(box_node.op.body)
            for qubit, single_qubit_run in per_qubit_runs.items():
                # convert the outer qubit to the corresponding qubit in the box's circuit
                box_qubit = box_dag.qubits[box_node.qargs.index(qubit)]
                # finally, loop through the run, add to the box dag and remove from the outer dag
                for node in single_qubit_run[::-1]:
                    box_dag.apply_operation_front(node.op, qargs=[box_qubit])
                    dag.remove_op_node(node)

            # the new box content is ready, replace the old box
            new_box = BoxOp(
                body=dag_to_circuit(box_dag),
                label=box_node.op.label,
                annotations=box_node.op.annotations,
            )
            dag.substitute_node(box_node, new_box)

        return dag
