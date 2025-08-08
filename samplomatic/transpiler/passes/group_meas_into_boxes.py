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

"""GroupMeasIntoBoxes"""

from collections import defaultdict

from qiskit.circuit import Clbit, Instruction, Qubit
from qiskit.dagcircuit import DAGCircuit, DAGOpNode
from qiskit.transpiler.basepasses import TransformationPass
from qiskit.transpiler.exceptions import TranspilerError

from .utils import asap_topological_nodes, make_and_insert_box, validate_op_is_supported


class GroupMeasIntoBoxes(TransformationPass):
    """Collect the measuremnts in a circuit inside left-dressed boxes.

    This pass collects all of the measurements in the input circuit in left-dressed boxes, together
    with the single-qubit gates that preceed them. To assign the measurements to these boxes, it
    uses a greedy collection strategy that tries to collect measurements in the earliest possible
    box that they can fit.

    .. note::
        Barriers, boxes, and multi-qubit gates that are present in the input circuit act as
        delimiters. This means that when one of these delimiters stands between a group of
        single-qubit gates and a measurement, those single-qubit gates are not added to the box.
    """

    def __init__(self):
        TransformationPass.__init__(self)

    def run(self, dag: DAGCircuit) -> DAGCircuit:
        """Collect the operations in the dag inside left-dressed boxes."""
        # A map to temporarily store single-qubit gates before inserting them into a box
        cached_gates_1q: dict[Qubit, list[Instruction]] = defaultdict(list)

        # The nodes to be added to the current box
        nodes_current_box: list[DAGOpNode] = []

        # The qubits that are active within the current box.
        # Note: A qubit is marked as "active" when within the current box, there is a measurement
        # gate acting on it. Therefore, active qubits are no longer willing to receive measurements
        # within the current box.
        active_qubits: set[Qubit] = set()

        # The clbits of the measurements in the current box.
        clbits: set[Clbit] = set()

        # The qubits barred by a delimiter.
        barred_qubits: set[Qubit] = set()

        for node in asap_topological_nodes(dag):
            validate_op_is_supported(node)

            if (name := node.op.name) in ["barrier", "box"] or node.op.num_qubits > 1:
                # If `node` contains a barrier, a box, or a multi-qubit gates, flush the
                # single-qubit gates.
                for qarg in node.qargs:
                    cached_gates_1q.pop(qarg, [])
                barred_qubits = barred_qubits.union(node.qargs)
            elif name == "measure":
                if any(carg in clbits for carg in node.cargs):
                    raise TranspilerError(
                        "Cannot twirl more than one measurement on the same classical bit."
                    )

                # Make a box if the node's qubits are already active, or if a delimiter is
                # present between this node and the previous ones
                make_box = any(qarg in active_qubits for qarg in node.qargs)
                make_box |= (not barred_qubits.isdisjoint(active_qubits)) and (
                    not barred_qubits.isdisjoint(node.qargs)
                )
                if make_box:
                    # If `node` overlaps with one or more active qubits, make and insert the box
                    make_and_insert_box(dag, nodes_current_box, active_qubits, clbits)

                    # Reset trackers
                    nodes_current_box = []
                    barred_qubits.difference_update(active_qubits)
                    active_qubits.clear()
                    clbits.clear()

                # If `node` contains a measurement:
                # - mark its qubit as active, store its clbit
                # - flush the single-qubit gates for its qubit
                # - append it to the list of nodes that will be added to current box
                active_qubits.add(qarg := node.qargs[0])
                clbits.add(node.cargs[0])
                barred_qubits.discard(qarg)
                nodes_current_box += cached_gates_1q.pop(qarg, [])
                nodes_current_box.append(node)
            elif node.op.num_qubits == 1:
                # If `node` contains a single-qubit gate, cache it.
                cached_gates_1q[node.qargs[0]].append(node)
            else:
                raise TranspilerError(f"``{name}`` operation is not supported.")

        # make the final multi-qubit gate left-dressed box
        make_and_insert_box(dag, nodes_current_box, active_qubits, clbits)

        return dag
