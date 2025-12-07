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

from qiskit.circuit import Bit
from qiskit.dagcircuit import DAGCircuit
from qiskit.transpiler.basepasses import TransformationPass
from qiskit.transpiler.exceptions import TranspilerError

from ...aliases import DAGOpNode
from .utils import make_and_insert_box, validate_op_is_supported


class GroupGatesIntoBoxes(TransformationPass):
    """Collect the two-qubit gates in a circuit inside left-dressed boxes.

    This pass collects all 2-qubit gates in the input circuit into left-dressed boxes. To assign the
    gates to these boxes, it uses a greedy collection strategy that tries to collect gates in the
    earliest possible box that they can fit.

    .. note::
        Barriers and boxes that are present in the input circuit act as delimiters. This means that
        when the pass encounters one of these delimiters acting on a subset of qubits, it
        immediately terminates the collection for those qubits and flushes the collected gates into
        a left-dressed box. The delimiters themselves remain present in the output circuit, but are
        placed outside of any boxes.

    .. note::
        Measurements also act as delimiters.

    .. note::
        The circuits returned by this pass may not be buildable. To make them buildable, one can
        either use :class`~.AddTerminalRightDressedBoxes` to add right-dressed "collector" boxes.
    """

    def run(self, dag: DAGCircuit) -> DAGCircuit:
        """Collect the operations in the dag inside left-dressed boxes.

        The collection strategy undertakes the following steps:
            *   Loop through the DAG's op nodes in topological order.
            *   Group together two-qubit gate nodes that need to be placed in the same box.
            *   Whenever a node can be placed in more than one group, place it in the earliest
                possible group--where "earliest" is with reference to topological ordering.
            *   When looping is complete, replace each group with a box.
        """
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
                    group_indices[qubit] = group_idx + 1
            elif name == "measure":
                # Flush the single-qubit gate nodes without placing them in a group
                qubit = node.qargs[0]
                clbit = node.cargs[0]

                group_indices[qubit] = group_indices[clbit] = group_idx
            elif node.is_standard_gate() and node.op.num_qubits == 1:
                # Leave single-qubit gates alone
                continue
            elif node.is_standard_gate() and node.op.num_qubits == 2:
                # Flush the two-qubit gate nodes into a group
                groups[group_idx].append(node)

                # Update trackers
                for qubit in node.qargs:
                    group_indices[qubit] = group_idx + 1
            else:
                raise TranspilerError(f"'{name}' operation is not supported.")

        for nodes in groups.values():
            make_and_insert_box(dag, nodes)

        return dag
