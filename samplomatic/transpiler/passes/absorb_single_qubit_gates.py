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


class AbsorbSingleQubitGates(TransformationPass):
    """Absorb all chains of single-qubit gates that are left of a box instruction into the box.

    Any instruction that is not a single-qubit gate, including measurements, entanglers, barriers,
    and boxes, is considered an interruption and ends a chain. For example, if an X, a
    measurement, a Y, and a Z gate precede a box in this order, then the Y and the Z will be
    absorbed into the box, but the X and the measurement will not.
    """

    def run(self, dag: DAGCircuit) -> DAGCircuit:
        """Perform rightwards absorption of chains of single-qubit gates."""
        # we collect runs of single qubit gates, organized by the qubit they act on. these
        # have the correct circuit order because we'll be looping te circuit topologically
        single_qubit_runs: dict[Qubit, list[DAGOpNode]] = defaultdict(list)

        for node in dag.topological_op_nodes():
            if node.is_standard_gate() and node.op.num_qubits == 1:
                single_qubit_runs[node.qargs[0]].append(node)

            elif node.op.name == "box":
                # since looping in topological order, if we encounter a box, we must have already
                # traversed all single-qubit gates that might precede it.
                box_dag = circuit_to_dag(node.op.body)
                for idx_qubit, box_qubit in enumerate(node.qargs):
                    # loop through the run, add to the box dag and remove from the outer dag
                    box_body_qubit = box_dag.qubits[idx_qubit]
                    single_qubit_run = single_qubit_runs[box_qubit]
                    for sq_node in single_qubit_run[::-1]:
                        box_dag.apply_operation_front(sq_node.op, qargs=[box_body_qubit])
                        dag.remove_op_node(sq_node)

                    single_qubit_run.clear()

                # the new box content is ready, replace the old box
                new_box = BoxOp(
                    body=dag_to_circuit(box_dag),
                    label=node.op.label,
                    annotations=node.op.annotations,
                )
                dag.substitute_node(node, new_box)

            else:
                # any existing single-qubit gates on these qubits can't ever be moved into a box
                for qubit in node.qargs:
                    single_qubit_runs[qubit].clear()

        return dag
