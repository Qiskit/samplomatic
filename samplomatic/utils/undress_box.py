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

"""undress_box"""

from collections import defaultdict
from copy import deepcopy

from qiskit.circuit import BoxOp, Instruction, QuantumCircuit, Qubit
from qiskit.converters import circuit_to_dag

from ..annotations import Twirl
from .get_annotation import get_annotation


def undress_box(box: BoxOp) -> BoxOp:
    """Return a box equivalent to ``box``, stripped of the single-qubit gates on the dressing side.

    This function removes all the single-qubit gates that can be pushed to the side indicated by its
    dressing (left or right) without encountering any other operation. If the input box contains no
    ``Twirl`` annotation, an unmodified copy of it is returned.

    The returned box owns a copy of all the annotations present in the given ``box``.

    Args:
        box: The box to remove the single-qubit gates from.
    """
    if not (twirl_annotation := get_annotation(box, Twirl)):
        return box.copy()

    return (
        undress_left_dressed_box(box)
        if twirl_annotation.dressing == "left"
        else undress_right_dressed_box(box)
    )


def undress_left_dressed_box(box: BoxOp) -> BoxOp:
    """Return a box equivalent to ``box``, stripped of the single-qubit gates on the left side.

    This function removes all the single-qubit gates that can be pushed to the left-hand side of
    the given box without encountering any other operation.

    Args:
        box: The box to remove the single-qubit gates from.
    """
    dag = circuit_to_dag(box.body)
    new_content = QuantumCircuit(box.body.qubits + box.body.clbits)

    active_qubits = set()
    for node in dag.topological_op_nodes():
        if node.is_standard_gate() and node.num_qubits == 1:
            if node.qargs[0] not in active_qubits:
                continue
        active_qubits = active_qubits.union(node.qargs)
        new_content.append(node.op, node.qargs, node.cargs)

    annotations = deepcopy(box.annotations)
    return BoxOp(body=new_content, annotations=annotations)


def undress_right_dressed_box(box: BoxOp) -> BoxOp:
    """Return a box equivalent to ``box``, stripped of the single-qubit gates on the right side.

    This function removes all the single-qubit gates that can be pushed to the right-hand side of
    the given box without encountering any other operation.

    Args:
        box: The box to remove the single-qubit gates from.
    """
    # A map to temporarily store single-qubit gates before inserting them into a box
    cached_gates_1q: dict[Qubit, list[Instruction]] = defaultdict(list)

    dag = circuit_to_dag(box.body)
    new_content = QuantumCircuit(box.body.qubits + box.body.clbits)

    for node in dag.topological_op_nodes():
        if node.is_standard_gate() and node.num_qubits == 1:
            # If `node` contains a one-qubit gate, cache it
            cached_gates_1q[node.qargs[0]].append(node)
        else:
            # Otherwise, flush the cache, then append the node's operation
            for qarg in node.qargs:
                for node_gate_1q in cached_gates_1q.pop(qarg, []):
                    new_content.append(node_gate_1q.op, node_gate_1q.qargs)
            new_content.append(node.op, node.qargs, node.cargs)

    annotations = deepcopy(box.annotations)
    return BoxOp(body=new_content, annotations=annotations)
