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

"""BoxKey"""

from collections.abc import Hashable

from qiskit.circuit import Clbit, Qubit
from qiskit.converters import circuit_to_dag

from ..aliases import CircuitInstruction, DAGOpNode
from ..constants import SYMMETRIC_2Q_GATES


class BoxKey:
    """An immutable snapshot of an instruction that owns a box, suitable for comparison and hashing.

    Instances of this class can be used, for example, as keys for a dictionary or as elements of a
    set. Mutating the original box does not mutate this class.

    At construction time, this class computes a standardized, immutable form of the instruction,
    which is the used when comparing two instances of this class, or when hashing one. In
    particular, this form is chosen so that properties such as instruction order within topological
    layers of the box, or order of symmetric instructions like ``"cz"`` are not relevant; we do not
    want ``cz(0, 1)`` and ``cz(1, 0)``, for example, to result in inequality or distinct hashes.

    Annotation comparison is unordered. It is assumed that all annotation types present are
    hashable (and consequently, immutable). Behavior is not defined when multiple equal annotations
    are present.

    Args:
        instruction: The instruction to create an immutable snapshot of.

    Raises:
        ValueError: If the instruction does not own a :class:`~.BoxOp`.
    """

    def __init__(self, instruction: CircuitInstruction):
        if instruction.name != "box":
            raise ValueError(
                "Expected an instruction that contains a 'box', found one that contains "
                f"'{instruction.name}'."
            )

        box = instruction.operation

        qubit_map = dict(zip(box.body.qubits, instruction.qubits))
        clbit_map = dict(zip(box.body.clbits, instruction.clbits))

        # Build hashable specifications for the operations in the box.
        nodes_specs = []
        for layer in circuit_to_dag(box.body).layers():
            layer_spec = frozenset(
                self._node_specs(node, qubit_map, clbit_map) for node in layer["graph"].op_nodes()
            )
            nodes_specs.append(layer_spec)
        nodes_specs = tuple(nodes_specs)

        # Build hashable specifications for the box's annotations.
        annotation_specs = frozenset(box.annotations)

        self._hashable_specs = (
            frozenset(instruction.qubits),
            frozenset(instruction.clbits),
            nodes_specs,
            annotation_specs,
        )
        self._hash = None

    def _node_specs(
        self, node: DAGOpNode, qubit_map: dict[Qubit, Qubit], clbit_map: dict[Clbit, Clbit]
    ) -> tuple[Hashable, Hashable, Hashable]:
        """Return hashable specifications for the given node.

        This function returns a tuple containing hashable specifications for the node's operation,
        parameters, and qubits.
        """
        op = node.op

        if not (node.is_standard_gate() or op.name in ["barrier", "measure"]):
            raise ValueError(f"Hashing of {op.name} is not supported.")

        op_hashable = (op.name, op.num_qubits, op.num_clbits)

        param_hashable = tuple(
            f"{param:.{8}f}" if isinstance(param, float) else param for param in op.params
        )

        qubit_hashable = tuple(qubit_map[qubit] for qubit in node.qargs)
        if op.name in SYMMETRIC_2Q_GATES:
            # Special handling for symmetric gates so that `qubit_hashable` does not depend on
            # qubit ordering
            qubit_hashable = frozenset(qubit_hashable)

        clbit_hashable = tuple(clbit_map[clbit] for clbit in node.cargs)

        return (op_hashable, param_hashable, qubit_hashable, clbit_hashable)

    def __hash__(self):
        if self._hash is None:
            self._hash = hash(self._hashable_specs)
        return self._hash

    def __eq__(self, other):
        return (
            isinstance(other, BoxKey)
            and hash(self) == hash(other)  # Fast return when ``self != other``
            and self._hashable_specs == other._hashable_specs
        )
