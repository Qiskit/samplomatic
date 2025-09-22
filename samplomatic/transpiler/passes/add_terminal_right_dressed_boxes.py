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

"""AddTerminalRightDressedBoxes"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from qiskit.circuit import BoxOp, Instruction, QuantumCircuit, Qubit
from qiskit.converters import circuit_to_dag
from qiskit.dagcircuit import DAGCircuit
from qiskit.transpiler.basepasses import TransformationPass

from ...annotations import BasisTransform, Twirl
from ...utils import get_annotation
from .utils import asap_topological_nodes, validate_op_is_supported


class AddTerminalRightDressedBoxes(TransformationPass):
    """Add right-dressed boxes to collect uncollected virtual gates emitted by left-dressed boxes.

    This pass adds right-dressed "collector" boxes to the given circuit to ensure that none of the
    virtual gates emitted by left-dressed boxes are left uncollected. Any group of single-qubit
    gates adjacent to a newly added right-dressed box is also placed inside the box.

    .. note::
        Given a circuit that contains only left-dressed boxes, this pass returns a circuit that can
        be successfully built.
    """

    def __init__(self):
        TransformationPass.__init__(self)

    def _insert_cached_1q_gates_and_measures(
        self,
        dag: DAGCircuit,
        cached_measures: dict[Qubit, list[Instruction]],
        cached_gates_1q: dict[Qubit, list[Instruction]],
        unmeasured_qubits: Iterable[Qubit] | None = None,
    ):
        """Insert cached single-qubit gates and measurements into a right-dressed box.

        Also inserts all of the one-qubit gates acting on the given ``unmeasured_qubits``.
        """
        if not cached_measures and not unmeasured_qubits:
            return

        measured_qubits = cached_measures.keys()
        unmeasured_qubits = set(unmeasured_qubits) if unmeasured_qubits else set()
        box_qubits = list(unmeasured_qubits.union(measured_qubits))

        qubit_map = {qubit: idx for (idx, qubit) in enumerate(box_qubits)}

        # Insert the box prior to the measurements
        content = QuantumCircuit(box_qubits)
        for node in [node for qubit in box_qubits for node in cached_gates_1q.pop(qubit, [])]:
            content.append(node.op, [qubit_map[qubit] for qubit in node.qargs])
        box = BoxOp(body=content, annotations=[Twirl(dressing="right", group="pauli")])
        dag.apply_operation_back(box, box_qubits)

        # Insert the measurements
        for qubit in list(measured_qubits):
            measure_node = cached_measures.pop(qubit)
            dag.apply_operation_back(measure_node.op, measure_node.qargs, measure_node.cargs)

    def _update_uncollected_qubits_for_box(self, node, uncollected_qubits) -> set[Qubit]:
        """Update ``uncollected_qubits`` for box nodes.

        Right-dressed boxes act as collectors, and the uncollected qubits are updated accordingly.
        On the contrary, left-dressed boxes act as collectors only on the qubits that they measure.
        """
        if not node.op.name == "box":
            return uncollected_qubits

        twirl = get_annotation(node.op, Twirl)
        basis_transform = get_annotation(node.op, BasisTransform)
        if twirl and twirl.dressing == "right":
            # Right-dressed boxes act as collectors
            uncollected_qubits = uncollected_qubits.difference(node.qargs)
        elif twirl or basis_transform:
            uncollected_qubits = uncollected_qubits.union(node.qargs)
            for sub_node in asap_topological_nodes(circuit_to_dag(node.op.body)):
                if sub_node.op.name == "measure":
                    # Measurements in a left-dressed box act as collectors
                    uncollected_qubits = uncollected_qubits.difference(sub_node.qargs)
        return uncollected_qubits

    def run(self, dag: DAGCircuit) -> DAGCircuit:
        """Add right-dressed boxes to collect the uncollected leftwards virtual gates emitted."""
        new_dag = dag.copy_empty_like()

        # A map to temporarily store single-qubit gates before inserting them into a box
        cached_gates_1q: dict[Qubit, list[Instruction]] = defaultdict(list)

        # A map to temporarily store unboxed measurements before inserting a box prior to them
        cached_measures: dict[Qubit, list[Instruction]] = defaultdict(list)

        # A record of the active qubits that need to be collected by a final right-dressed box
        uncollected_qubits: set[Qubit] = set()

        for node in asap_topological_nodes(dag):
            validate_op_is_supported(node)

            name = node.op.name

            if (node.is_standard_gate() and node.op.num_qubits == 1) or name == "measure":
                # If `node` contains a single-qubit gate or a measurement:
                # - If a cached measurement exists on that qubit, we flush the cache.
                # - If the qubit needs a collector, we store the node in the appropriate cache,
                #   otherwise we apply it to the dag.

                if (qubit := node.qargs[0]) in cached_measures:
                    uncollected_qubits.difference_update(cached_measures)
                    self._insert_cached_1q_gates_and_measures(
                        new_dag, cached_measures, cached_gates_1q
                    )

                if qubit in uncollected_qubits:
                    if name == "measure":
                        cached_measures[qubit] = node
                    else:
                        cached_gates_1q[qubit].append(node)
                else:
                    new_dag.apply_operation_back(node.op, node.qargs, node.cargs)

            else:
                # If `node` contains a multi-qubit gate, a box, or a barrier:
                # - We flush the cache, as nothing can cross over boxes, barriers, or multi-qubit
                #   gates.
                # - We apply the node's operation to the dag.
                # - If `node` contains a derssed box, we update `uncollected_qubits` accordingly
                uncollected_qubits.difference_update(cached_measures)
                self._insert_cached_1q_gates_and_measures(new_dag, cached_measures, cached_gates_1q)

                new_dag.apply_operation_back(node.op, node.qargs, node.cargs)

                uncollected_qubits = self._update_uncollected_qubits_for_box(
                    node, uncollected_qubits
                )

        # Add the final right-dressed box on all the qubits that remain uncollected
        unmeasured_qubits = uncollected_qubits.difference(cached_measures)
        self._insert_cached_1q_gates_and_measures(
            new_dag, cached_measures, cached_gates_1q, unmeasured_qubits
        )

        return new_dag
