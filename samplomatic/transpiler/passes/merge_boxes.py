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

"""MergeBoxes"""

from qiskit.circuit import BoxOp, QuantumCircuit, Qubit
from qiskit.dagcircuit import DAGCircuit, DAGOpNode
from qiskit.transpiler.basepasses import TransformationPass

from ...annotations import Twirl
from .utils import asap_topological_nodes, validate_op_is_supported


class MergeBoxes(TransformationPass):
    """
    Merge boxes containing only single-qubit gates with bordering boxes if possible.

    The boxes around single-qubit gates that are created due to a barrier-like operation to their
    right can be merged with a box to their right that contains all the first node's qargs.
    """

    def __init__(self):
        TransformationPass.__init__(self)

    def _merge_boxes(
        self,
        dag: DAGCircuit,
        boxes_to_merge: list[DAGOpNode],
        box_so_far_qargs: set[Qubit],
        right_box: DAGOpNode = None,
    ):
        """
        Adds contents of inputted boxes into a single box.

        Combines a batch of single-qubit-gate-containing boxes with a final box that cannot be
        combined with boxes to its right. If no final box is passed, the batch of boxes is merged
        on its own.
        """
        # this case actually occurs quite commonly, the way the ``run`` function is set up.
        if not boxes_to_merge:
            return

        # set up the circuit containing all the boxes' operations
        new_content = QuantumCircuit(list(box_so_far_qargs))
        if right_box:
            # this union operation exists for the case that the right box contains qubits that are
            # not already in any of the boxes to the left
            new_qargs = box_so_far_qargs.union(right_box.op.body.qubits)
            new_content = QuantumCircuit(list(new_qargs), right_box.op.body.clbits)

        # add the boxed operations to the circuit
        contains_right_dressed_box = False
        for left_box in boxes_to_merge:
            for op in left_box.op.body:
                new_content.append(op)
        if right_box:
            contains_right_dressed_box = right_box.op.annotations[0].dressing == "right"
            for op in right_box.op.body:
                new_content.append(op)

        # create a right-dressed box if the last box is right-dressed and apply to the dag
        dressing_direction = "right" if contains_right_dressed_box else "left"
        box = BoxOp(new_content, annotations=[Twirl(dressing=dressing_direction)])
        dag.apply_operation_back(box, new_content.qubits, new_content.clbits)

    def run(self, dag: DAGCircuit) -> DAGCircuit:
        """
        Finds boxes containing single-qubit gates and merges them when possible.
        """
        new_dag: DAGCircuit = dag.copy_empty_like()

        # collects batches of left-dressed single-qubit-gate-containing boxes and only merges them
        # when a node is found to terminate the batch:
        #
        boxes_to_merge: list[DAGOpNode] = []

        # the qubits covered by any box in the batch ``boxes_to_merge``
        box_so_far_qargs: set[Qubit] = set()

        for left_node in asap_topological_nodes(dag):
            validate_op_is_supported(left_node)

            # non-box operations are treated normally, but if they are in the way of a batch of
            # boxes, that batch is first merged and added to the dag before the non-box op
            if left_node.op.name != "box":
                if any(qarg in left_node.qargs for qarg in box_so_far_qargs):
                    self._merge_boxes(new_dag, boxes_to_merge, box_so_far_qargs, None)
                    boxes_to_merge = []
                    box_so_far_qargs = set()
                new_dag.apply_operation_back(left_node.op, left_node.qargs, left_node.cargs)
                continue

            is_1q_gate_box = all(
                (len(operation.qubits) == 1 and len(operation.clbits) == 0)
                for operation in left_node.op.body.data
            )
            is_last_box = not [node for node in dag.op_successors(left_node)]

            # another conditional that leads to a batch of boxes ending
            if not is_1q_gate_box or is_last_box or left_node.op.annotations[0].dressing == "right":
                if any(qarg in left_node.qargs for qarg in box_so_far_qargs):
                    self._merge_boxes(new_dag, boxes_to_merge, box_so_far_qargs, left_node)
                    boxes_to_merge = []
                    box_so_far_qargs = set()
                else:
                    self._merge_boxes(new_dag, boxes_to_merge, box_so_far_qargs, None)
                    new_dag.apply_operation_back(left_node.op, left_node.qargs, left_node.cargs)
                    boxes_to_merge = []
                    box_so_far_qargs = set()
                continue

            # adds boxes to the batch
            if is_1q_gate_box:
                boxes_to_merge.append(left_node)
                for qarg in left_node.qargs:
                    box_so_far_qargs.add(qarg)

        return new_dag
