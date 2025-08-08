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

"""Utils for transpiler module."""

from collections.abc import Iterator

from qiskit.circuit import BoxOp, Clbit, QuantumCircuit, Qubit
from qiskit.dagcircuit import DAGCircuit, DAGOpNode
from qiskit.transpiler.exceptions import TranspilerError

from ...annotations import DressingLiteral, Twirl


def asap_topological_nodes(dag: DAGCircuit) -> Iterator[DAGOpNode]:
    """Yield operation nodes of the DAG circuit in "asap" topological order.

    In this case, "asap" means that topological generations are filled greedily, and nodes are
    yielded out of these generations.

    Args:
        dag: The dag circuit to yield nodes from.

    Yields:
        Nodes from the dag circuit.
    """
    for layer in dag.multigraph_layers():
        yield from (node for node in layer if isinstance(node, DAGOpNode))


def make_and_insert_box(
    dag: DAGCircuit,
    nodes: list[DAGOpNode],
    active_qubits: set[Qubit],
    clbits: set[Clbit] = set(),
    dressing: DressingLiteral = "left",
) -> None:
    """Make a dressed box and insert it into a dag.

    Args:
        dag: The dag to insert the box into (modified in place).
        nodes: The nodes of ``dag`` to be placed in the box.
        active_qubits: The qubits that are active in the box being inserted.
        clbits: The clbits that are part of the ``cargs`` of an operation that is being added
            to the box.
        dressing: Whether the box is left- or right-dressed.
    """
    if not nodes:
        return

    qubit_map = {qubit: idx for (idx, qubit) in enumerate(active_qubits)}
    clbit_map = {clbit: idx for (idx, clbit) in enumerate(clbits)}

    content = QuantumCircuit(list(active_qubits), list(clbits))
    for node in nodes:
        content.append(
            node.op,
            [qubit_map[qarg] for qarg in node.qargs],
            [clbit_map[carg] for carg in node.cargs],
        )

    box = BoxOp(body=content, annotations=[Twirl(dressing=dressing, group="pauli")])
    dag.replace_block_with_op(nodes, box, qubit_map | clbit_map)


def validate_op_is_supported(node: DAGOpNode):
    """Raises if the given node contains an operation that is not supported by the transpiler.

    Args:
        node: The node to validate.

    Raises:
        TranspilerError: If node contains anything other than a box, a barrier, a measurement, or
        a gate.
    """
    if node.is_standard_gate() or node.op.name in ["box", "barrier", "measure"]:
        return
    raise TranspilerError(f"``'{node.op.name}'`` is not supported.")
