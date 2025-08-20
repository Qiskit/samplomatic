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

from qiskit.circuit import BoxOp, QuantumCircuit
from qiskit.dagcircuit import DAGCircuit, DAGOpNode
from qiskit.transpiler.basepasses import TransformationPass

from .utils import asap_topological_nodes


class MergeBoxes(TransformationPass):
    """
    Merge boxes containing only single-qubit gates with bordering boxes if possible.

    The boxes around single-qubit gates that are created due to a barrier-like operation to their
    right can be merged with a box to their right that contains all the first node's qargs.
    """

    def __init__(self):
        TransformationPass.__init__(self)

    def _mergeable(self, left_box: DAGOpNode, right_box: DAGOpNode):
        # empty cache should be mergeable with any box
        if not left_box:
            return True
        return set(left_box.op.annotations) == set(right_box.op.annotations)

    def _merge_boxes(self, dag: DAGCircuit, left_box: DAGOpNode, right_box: DAGOpNode):
        # if the cache is empty, merging just sets the cache equal to `right_box`
        if not left_box:
            return right_box

        combined_qargs = set(left_box.qargs).union(set(right_box.qargs))
        new_content = QuantumCircuit(list(combined_qargs), list(right_box.cargs))

        # prepending the left box's operations is for when there are 1q gates on qubits that both
        # boxes have in common
        for op in left_box.op.body:
            new_content.append(op)
        for op in right_box.op.body:
            new_content.append(op)

        box = BoxOp(new_content, annotations=left_box.op.annotations)
        return dag.apply_operation_back(box, new_content.qubits, new_content.clbits)

    def _conditional_clear_cache(
        self, dag: DAGCircuit, left_box: DAGOpNode, right_box: DAGOpNode, mergeable: bool
    ):
        if not left_box:
            return None

        # checks whether the right box contains only 1q gates
        is_1q_gate_box = right_box.op.name == "box" and all(
            (len(operation.qubits) == 1 and len(operation.clbits) == 0)
            for operation in right_box.op.body.data
        )

        if not mergeable or not is_1q_gate_box:
            dag.apply_operation_back(left_box.op, left_box.qargs, left_box.cargs)
            return None
        return left_box

    def run(self, dag: DAGCircuit) -> DAGCircuit:
        """
        Finds boxes containing single-qubit gates and merges them when possible.
        """
        # A dag where all operations are added except boxes that get merged into others
        new_dag: DAGCircuit = dag.copy_empty_like()

        # A cache storing the most recently merged boxes (that could potentially be merged with the
        # current node)
        merged_box_cache: DAGOpNode = None

        for node in asap_topological_nodes(dag):
            if node.op.name == "box":
                # if mergeable box, merge with cache and if possible clear the cache
                if self._mergeable(merged_box_cache, node):
                    merged_box_cache = self._merge_boxes(new_dag, merged_box_cache, node)
                    merged_box_cache = self._conditional_clear_cache(
                        new_dag, merged_box_cache, node, True
                    )

                # if unmergeable box, clear the cache if possible and update the with the new node
                else:
                    merged_box_cache = self._conditional_clear_cache(
                        new_dag, merged_box_cache, node, False
                    )
                    merged_box_cache = self._merge_boxes(new_dag, merged_box_cache, node)
            else:
                # if non-box node, it acts as a barrier, so clear the cache and apply afterwards
                if merged_box_cache and any(qarg in merged_box_cache.qargs for qarg in node.qargs):
                    merged_box_cache = self._conditional_clear_cache(
                        new_dag, merged_box_cache, node, False
                    )
                new_dag.apply_operation_back(node.op, node.qargs, node.cargs)

        # add remaining boxes that were not 2q, meas, or unmergeable boxes at the end of the circuit
        merged_box_cache = self._conditional_clear_cache(new_dag, merged_box_cache, node, False)
        return new_dag
