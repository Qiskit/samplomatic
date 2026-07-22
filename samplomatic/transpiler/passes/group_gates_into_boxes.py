# This code is a Qiskit project.
#
# (C) Copyright IBM 2025, 2026.
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
from collections.abc import Iterable
from typing import Literal

from qiskit.circuit import Annotation, Bit
from qiskit.dagcircuit import DAGCircuit
from qiskit.transpiler.basepasses import TransformationPass
from qiskit.transpiler.exceptions import TranspilerError

from ...aliases import DAGOpNode
from ...annotations import Twirl
from ...utils import validate_literals
from .utils import (
    alap_topological_nodes,
    asap_topological_nodes,
    make_and_insert_box,
    validate_op_is_supported,
)


class GroupGatesIntoBoxes(TransformationPass):
    """Collect the two-qubit gates in a circuit inside left-dressed boxes.

    This pass collects all 2-qubit gates in the input circuit into left-dressed boxes. To assign
    the gates to these boxes, it uses a greedy collection strategy. By default (``strategy="asap"``)
    it places each gate in the earliest possible box. When ``strategy="alap"`` it places each gate
    in the latest possible box.

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
        either use :class:`~.AddTerminalRightDressedBoxes` to add right-dressed "collector" boxes.
    """

    @validate_literals("strategy")
    def __init__(
        self,
        annotations: Iterable[Annotation] = (Twirl(),),
        strategy: Literal["asap", "alap"] = "asap",
    ):
        super().__init__()
        self.annotations = list(annotations)
        self.strategy = strategy

    def run(self, dag: DAGCircuit) -> DAGCircuit:
        """Collect the operations in the dag inside left-dressed boxes.

        The collection strategy undertakes the following steps:
            *   Loop through the DAG's op nodes in topological order (ASAP) or reverse topological
                order (ALAP).
            *   Group together two-qubit gate nodes that need to be placed in the same box.
            *   Whenever a node can be placed in more than one group, place it in the earliest
                possible group (ASAP) or the latest possible group (ALAP).
            *   When looping is complete, replace each group with a box.
        """
        if self.strategy == "alap":
            return self._run_alap(dag)
        return self._run_asap(dag)

    def _run_asap(self, dag: DAGCircuit) -> DAGCircuit:
        # A list of groups that need to be placed in the same box, expressed as a dict for fast
        # access. Every node in each group either contains a single- or two-qubit gate--when
        # constructing this dictionary, we explicitly leave out nodes that contain different ops
        groups: dict[int, list[DAGOpNode]] = defaultdict(list)

        # A map from bits (qubits and clbits) to the index of the earliest group that is able to
        # collect operations on those bits
        group_indices: dict[Bit, int] = defaultdict(int)

        for node in asap_topological_nodes(dag):
            validate_op_is_supported(node)

            # The index of the earliest group able to collect ops on all the bits in this node.
            # default=0 protects against ops with no qargs and no cargs (e.g. a zero-width barrier).
            group_idx: int = max((group_indices[bit] for bit in node.qargs + node.cargs), default=0)

            if (name := node.op.name) in ["barrier", "box"]:
                # Flush the single-qubit gate nodes and place them in a group
                for qubit in node.qargs:
                    group_indices[qubit] = group_idx + 1
            elif name == "measure":
                # Flush the single-qubit gate nodes without placing them in a group
                qubit = node.qargs[0]
                clbit = node.cargs[0]

                group_indices[qubit] = group_indices[clbit] = group_idx
            elif node.is_standard_gate() and node.op.num_qubits <= 1:
                # Leave zero- and single-qubit gates alone (global phase gate is 0 qubits)
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
            make_and_insert_box(dag, nodes, annotations=self.annotations)

        return dag

    def _run_alap(self, dag: DAGCircuit) -> DAGCircuit:
        # Same structure as _run_asap but traversal is reversed: we iterate from the end of the
        # circuit backward, and each gate is assigned to the latest group it can fit in.
        groups: dict[int, list[DAGOpNode]] = defaultdict(list)

        # A map from bits to the index of the latest group that is able to collect ops on those
        # bits (starts at 0 and decrements as gates are assigned)
        group_indices: dict[Bit, int] = defaultdict(int)

        for node in alap_topological_nodes(dag):
            validate_op_is_supported(node)

            # The index of the latest group able to collect ops on all the bits in this node
            group_idx: int = min(group_indices[bit] for bit in node.qargs + node.cargs)

            if (name := node.op.name) in ["barrier", "box"]:
                # Flush: push the boundary one step earlier for all affected qubits
                for qubit in node.qargs:
                    group_indices[qubit] = group_idx - 1
            elif name == "measure":
                qubit = node.qargs[0]
                clbit = node.cargs[0]

                group_indices[qubit] = group_indices[clbit] = group_idx
            elif node.is_standard_gate() and node.op.num_qubits == 1:
                continue
            elif node.is_standard_gate() and node.op.num_qubits == 2:
                groups[group_idx].append(node)

                for qubit in node.qargs:
                    group_indices[qubit] = group_idx - 1
            else:
                raise TranspilerError(f"'{name}' operation is not supported.")

        # Sort by ascending key so boxes are inserted in left-to-right circuit order
        for nodes in dict(sorted(groups.items())).values():
            make_and_insert_box(dag, nodes, annotations=self.annotations)

        return dag
