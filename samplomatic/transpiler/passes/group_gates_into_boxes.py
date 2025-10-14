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

from __future__ import annotations

from collections import defaultdict

from qiskit.circuit import Bit, Qubit
from qiskit.dagcircuit import DAGCircuit
from qiskit.transpiler.basepasses import TransformationPass
from qiskit.transpiler.exceptions import TranspilerError

from ...aliases import DAGOpNode
from .utils import make_and_insert_box, validate_op_is_supported


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

        The collection strategy undertakes the following steps:
            *   Loop through the DAG's op nodes in topological order.
            *   Group together single- and two-qubit gate nodes that need to be placed in the same
                box.
            *   Whenever a node can be placed in more than one group, place it in the earliest
                possible group--where "earliest" is with reference to topological ordering.
            *   When looping is complete, replace each group with a box.
        """
        # A map to temporarily store single-qubit gate nodes before inserting them into a group
        cached_gates_1q: dict[Qubit, list[DAGOpNode]] = defaultdict(list)

        # A list of groups that need to be placed in the same box, expressed as a dict for fast
        # access. Every node in each group either contains a single- or two-qubit gate--when
        # constructing this dictionary, we explicitly leave out nodes that contain different ops
        groups: dict[int, list[DAGOpNode]] = defaultdict(list)

        # A map from bits (qubits and clbits) to the index of the earliest group that is able to
        # collect operations on those bits
        group_indices: dict[Bit, int] = defaultdict(int)

        for node in dag.topological_op_nodes():
            validate_op_is_supported(node)

            # The index of the earliest group able to collect ops on all the bits in this node
            group_idx: int = max(group_indices[bit] for bit in node.qargs + node.cargs)

            if (name := node.op.name) in ["barrier", "box"]:
                # Flush the single-qubit gate nodes and place them in a group
                for qubit in node.qargs:
                    groups[group_idx] += cached_gates_1q.pop(qubit, [])
                    group_indices[qubit] = group_idx + 1
            elif name == "measure":
                # Flush the single-qubit gate nodes without placing them in a group
                qubit = node.qargs[0]
                clbit = node.cargs[0]

                cached_gates_1q.pop(qubit, [])
                group_indices[qubit] = group_indices[clbit] = group_idx
            elif node.is_standard_gate() and node.op.num_qubits == 1:
                # Cache the node
                cached_gates_1q[node.qargs[0]].append(node)
            elif node.is_standard_gate() and node.op.num_qubits == 2:
                # Flush the cached single- and two-qubit gate nodes into a group
                for qubit in node.qargs:
                    groups[group_idx] += cached_gates_1q.pop(qubit, [])
                groups[group_idx].append(node)

                # Update trackers
                for qubit in node.qargs:
                    group_indices[qubit] = group_idx + 1
            else:
                raise TranspilerError(f"'{name}' operation is not supported.")

        for nodes in groups.values():
            make_and_insert_box(dag, nodes)

        return dag
