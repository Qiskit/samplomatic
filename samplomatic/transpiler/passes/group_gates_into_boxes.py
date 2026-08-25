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
from enum import IntEnum
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


class _TraversalDirection(IntEnum):
    """The direction the DAG is scanned in.

    Expressed as the offset applied to a group index each time a boundary is pushed further along
    the traversal.
    """

    FORWARD = 1
    BACKWARD = -1


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
        Measurements and resets also act as delimiters.

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
            return self._run(dag, alap_topological_nodes(dag), _TraversalDirection.BACKWARD)
        return self._run(dag, asap_topological_nodes(dag), _TraversalDirection.FORWARD)

    def _run(
        self, dag: DAGCircuit, ordered_nodes: Iterable[DAGOpNode], direction: _TraversalDirection
    ) -> DAGCircuit:
        # A list of groups that need to be placed in the same box
        groups: dict[int, list[DAGOpNode]] = defaultdict(list)

        # A map from bits to the index of the group that is able to collect operations on those bits
        group_indices: dict[Bit, int] = defaultdict(int)

        # How to compare groups in different traversal directions
        pick_group = max if direction == _TraversalDirection.FORWARD else min

        for node in ordered_nodes:
            validate_op_is_supported(node)

            # The index of the group able to collect ops on all the bits in this node
            group_idx: int = pick_group(
                (group_indices[bit] for bit in node.qargs + node.cargs), default=0
            )

            if (name := node.op.name) in ["barrier", "box"]:
                # Flush: push the boundary one step further in the traversal direction
                for qubit in node.qargs:
                    group_indices[qubit] = group_idx + direction
            elif name.startswith("meas"):
                # Flush the single-qubit gate nodes without placing them in a group
                qubit = node.qargs[0]
                clbit = node.cargs[0]

                group_indices[qubit] = group_indices[clbit] = group_idx
            elif name.startswith("reset"):
                group_indices[node.qargs[0]] = group_idx
            elif name == "delay":
                continue
            elif node.is_standard_gate() and node.op.num_qubits <= 1:
                # Leave zero- and single-qubit gates alone (global phase gate is 0 qubits)
                continue
            elif node.is_standard_gate() and node.op.num_qubits == 2:
                # Flush the two-qubit gate nodes into a group
                groups[group_idx].append(node)

                # Update trackers
                for qubit in node.qargs:
                    group_indices[qubit] = group_idx + direction
            else:
                raise TranspilerError(f"'{name}' operation is not supported.")

        # Sort by ascending key so boxes are inserted in left-to-right circuit order
        for nodes in dict(sorted(groups.items())).values():
            make_and_insert_box(dag, nodes, annotations=self.annotations)

        return dag
