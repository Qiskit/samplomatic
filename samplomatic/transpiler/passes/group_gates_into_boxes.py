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

"""GroupGatesIntoBoxes"""

from collections import defaultdict

from qiskit.circuit import Instruction, Qubit
from qiskit.dagcircuit import DAGCircuit, DAGOpNode
from qiskit.transpiler.basepasses import TransformationPass

from .utils import asap_topological_nodes, make_and_insert_box, validate_op_is_supported


class GroupGatesIntoBoxes(TransformationPass):
    """Collect the gates in a circuit inside left-dressed boxes.

    This pass collects all of the gates in the input circuit in left-dressed boxes. Each box in the
    returned circuit contains potentially multiple single-qubit gates followed by a layer of
    multi-qubit gates. To assign the gates to these boxes, it uses a greedy collection strategy that
    tries to collect gates in the earliest possible box that they can fit. In addition to the left-
    dressed boxes, the pass also adds a right-dressed box at the end of the circuit to collect
    virtual gates.

    .. note::
        Barriers and boxes that are present in the input circuit act as delimiters. This means that
        when the pass encounters one of these delimiters acting on a subset of qubits, it
        immediately terminates the collection for those qubits and flushes the collected gates into
        a left-dressed box. The delimiters themselves remain present in the output circuit, but are
        placed outside of any boxes.

    .. note::
        Measurements also act as delimiters. However, any group of single-qubit gates that preceed
        the measurements are left unboxed. This allows grouping these single-qubit gates in an
        optimal way with a subsequent pass, depending on whether the user wants to also group the
        measurements into boxes and on their grouping strategy.

    .. note::
        The circuits returned by this pass may not be buildable. To make them buildable, one can
        either use :class`~.AddTerminalRightDressedBoxes` to add right-dressed "collector" boxes.
    """

    def __init__(self):
        TransformationPass.__init__(self)

    def run(self, dag: DAGCircuit) -> DAGCircuit:
        """Collect the operations in the dag inside left-dressed boxes.

        Each left-dressed box contains a non-zero number of multi-qubit gates that can only
        be applied to non-overlapping sets of qubits. Each box also includes all the single-
        qubit gates that precede the multi-qubit gates on overlapping qubits that haven't been
        collected in a box.
        """
        # A map to temporarily store single-qubit gates before inserting them into a box
        cached_gates_1q: dict[Qubit, list[Instruction]] = defaultdict(list)

        # The nodes to be added to the current box
        nodes_current_box: list[DAGOpNode] = []

        # The qubits that are active within the current box.
        # Note: A qubit is marked as "active" when within the current box, there is a multi-qubit
        # gate acting on it. Therefore, active qubits are no longer willing to receive gates
        # within the current box.
        active_qubits: set[Qubit] = set()

        # The qubits barred by a delimiter.
        barred_qubits: set[Qubit] = set()

        for node in asap_topological_nodes(dag):
            validate_op_is_supported(node)

            if (name := node.op.name) in ["barrier", "box"]:
                # If `node` contains a barrier or a box, collect the cached single-qubit gates into
                # a left-dressed box.
                nodes_1q_gates = []
                qargs_1q_gates = []
                for qarg in node.qargs:
                    nodes_1q_gates += (gates_1q := cached_gates_1q.pop(qarg, []))
                    if gates_1q:
                        qargs_1q_gates += [qarg]

                make_and_insert_box(dag, nodes_1q_gates, qargs_1q_gates)

                # Update the trackers
                barred_qubits = barred_qubits.union(node.qargs)
            elif name == "measure":
                # If `node` contains a measurement, flush the single-qubit gates without placing
                # them in a box.
                qarg = node.qargs[0]
                cached_gates_1q.pop(qarg, [])

                # Update the trackers
                barred_qubits.add(qarg)
            elif node.op.num_qubits == 1:
                # If `node` contains a single-qubit gate, cache it.
                cached_gates_1q[node.qargs[0]].append(node)
            else:
                # Make a box if the node's qubits are already active, or if a delimiter is
                # present between this node and the previous ones
                make_box = any(qarg in active_qubits for qarg in node.qargs)
                make_box |= (not barred_qubits.isdisjoint(active_qubits)) and (
                    not barred_qubits.isdisjoint(node.qargs)
                )
                if make_box:
                    # If `node` overlaps with one or more active qubits, make and insert the box
                    make_and_insert_box(dag, nodes_current_box, active_qubits)

                    # Reset trackers
                    nodes_current_box = []
                    barred_qubits.difference_update(active_qubits)
                    active_qubits.clear()

                # If `node` contains a multi-qubit gate:
                # - mark its qubits as active
                # - flush the single-qubit gates for its qubits
                # - append it to the list of nodes that will be added to current box
                for qarg in node.qargs:
                    active_qubits.add(qarg)
                    nodes_current_box += cached_gates_1q.pop(qarg, [])
                    barred_qubits.discard(qarg)
                nodes_current_box.append(node)

        # make the final multi-qubit gate left-dressed box
        make_and_insert_box(dag, nodes_current_box, active_qubits)

        return dag
