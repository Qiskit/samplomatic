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

from collections.abc import Iterable
from dataclasses import dataclass

from qiskit.circuit import BoxOp, QuantumCircuit, Qubit
from qiskit.dagcircuit import DAGCircuit, DAGOpNode
from qiskit.transpiler.basepasses import TransformationPass

from ...annotations import ChangeBasis, Twirl
from ...utils import get_annotation
from .utils import validate_op_is_supported

_EMPTY_SET = frozenset(())


def _inverse_box_qubit_map(box_node: DAGOpNode) -> dict[Qubit, Qubit]:
    return {box_qubit: qubit for qubit, box_qubit in zip(box_node.qargs, box_node.op.body.qubits)}


@dataclass(slots=True)
class BoxLayers:
    layers: list[list[DAGOpNode]]
    """List of layers of empty right-dressed boxes.

    Here, a "layer" has the defining characteristic that they are safe to be eventually merged into
    a single box. This means that, for example, they can't be partially separated by a barrier
    anywhere.
    """

    last_layer_qubits: set[Qubit]
    """All qubits targeted by the last element of `layers`."""

    def add_box(self, box_node: DAGOpNode):
        """Add a box to an eligible layer."""
        if self.last_layer_qubits.isdisjoint(box_node.qargs):
            self.layers[-1].append(box_node)
        else:
            self.layers.append([box_node])
            self.last_layer_qubits.clear()
        self.last_layer_qubits.update(box_node.qargs)

    def maybe_start_new_layer(self, qubits: Iterable[Qubit]):
        """Signal that some qubits might block layer accumulation."""
        # we only need to worry about a partial overlap, since in the case of a full-overlap,
        # future boxes added are still compatible with being joined to the last layer
        if not (
            self.last_layer_qubits.isdisjoint(qubits) or self.last_layer_qubits.issuperset(qubits)
        ):
            self.last_layer_qubits.clear()
            self.layers.append([])


class AddTerminalRightDressedBoxes(TransformationPass):
    """Add right-dressed boxes to collect uncollected virtual gates emitted by left-dressed boxes.

    .. note::

        All boxes added by this pass are empty, so consider combining this pass with
        :class:`AbsorbSingleQubitGates` if you would like nearby single-qubit gates to be placed
        into the boxes this pass adds.
    """

    @classmethod
    def _new_box(cls, qubits: Iterable[Qubit], qubit_map: dict[Qubit, int]) -> BoxOp:
        # we go a bit out of our way to use the same qubit instances as the original circuit and
        # also to sort them. neither of these steps is necessary, however, the former makes writing
        # tests more convenient because it makes it easier to use built-in circuit equality, and
        # the latter minimizes surprise to users.
        qubits = sorted(qubits, key=qubit_map.get)
        body = QuantumCircuit(qubits)
        return qubits, BoxOp(body=body, annotations=[Twirl(dressing="right", group="pauli")])

    @classmethod
    def _get_terminal_qubits(cls, node: DAGOpNode) -> tuple[set[Qubit], set[Qubit], set[Qubit]]:
        """Determine which qubits the node act on should be terminated now, or terminated later.

        A termination can either be done by some dressed box already in the circuit, or by a new
        box introduced by this pass. It is assumed by this method that all qubits the node act
        on might currently be unterminated; it is up to the caller to intersect them with those
        qubits that actually are unterminated to avoid attempting, for example, to terminate a
        qubit that doesn't actually require it.

        Args:
            node: The node to terminate.

        Returns:
            A triple of sets respectively representing:
             * Those qubits that, if active, must be terminated now by adding a right-dressed box.
             * Those qubits that should become active, if not already.
             * Those qubits that the given operation presently terminates, without intervention.
        """
        if node.is_standard_gate() and node.op.num_qubits == 1:
            # single qubit gates outside of a box are re-applied without further consideration
            return _EMPTY_SET, _EMPTY_SET, _EMPTY_SET

        if node.op.name == "box":
            # boxes need special treatment depending on annotations
            if (twirl := get_annotation(node.op, Twirl)) and twirl.dressing == "right":
                # right-dressed boxes terminate uncollected qubits unconditionally
                return _EMPTY_SET, _EMPTY_SET, set(node.qargs)

            if twirl or get_annotation(node.op, ChangeBasis):
                # left-dressed boxes terminate uncollected qubits on all qubits they measure
                # internally (twirled measurements), but they create/continue uncollected qubits
                # elsewhere. first, traverse the box and see which qubits are measured.
                measured_qubits = set()
                qubit_map = None  # don't compute this unless necessary
                for instr in node.op.body:
                    if instr.operation.name == "measure":
                        qubit_map = qubit_map or (qubit_map := _inverse_box_qubit_map(node))
                        measured_qubits.update(qubit_map[qubit] for qubit in instr.qubits)

                return _EMPTY_SET, set(node.qargs).difference(measured_qubits), measured_qubits

            # an un-annotated box might contain stuff that we can't propagate through, so
            # it is safest to just terminate now. ambitious readers of this code could update
            # it to be less lazy and traverse the contents to find out.
            return set(node.qargs), _EMPTY_SET, _EMPTY_SET

        if node.op.name == "barrier":
            # it's always okay to postpone termination until after a barrier
            return _EMPTY_SET, _EMPTY_SET, _EMPTY_SET

        # we treat every other kind of operation (multi-qubit gates, measurements, etc.) as "unsafe"
        # by forcing a termination on all of their qubits. note that there is room to be slightly
        # less restrictive here in the future, for example, by adding a case above to let all gates
        # live outside of boxes.
        return set(node.qargs), _EMPTY_SET, _EMPTY_SET

    def run(self, dag: DAGCircuit) -> DAGCircuit:
        """Add right-dressed boxes to collect the uncollected leftwards virtual gates emitted."""
        new_dag = dag.copy_empty_like()

        # this keeps track of which new boxes we'll merge together at the end into a single new box
        layers = BoxLayers([[]], set())

        # qubits that will eventually need to be terminated by a right-dressed box
        unterminated_qubits: set[Qubit] = set()

        # this just helps sorting qubits when creating new boxes
        all_qubits = {qubit: idx for idx, qubit in enumerate(dag.qubits)}

        # first, we traverse the circuit and place right-dressed boxes everywhere we think that
        # they are necessary, without attempting to minimize the total number of boxes inserted.
        # however, we do remember all boxes that we insert along with information about which ones
        # can eventually be grouped together
        for node in dag.topological_op_nodes():
            validate_op_is_supported(node)
            # determine the behaviour of this particular node
            terminate_now, terminate_later, terminated_by_this_op = self._get_terminal_qubits(node)

            # update our states of information, and insert a new box before the node if necessary
            if qubits := unterminated_qubits.intersection(terminate_now):
                qargs, box = self._new_box(qubits, all_qubits)
                box_node = new_dag.apply_operation_back(box, qargs, [])
                layers.add_box(box_node)
                unterminated_qubits.difference_update(qubits)
            unterminated_qubits.update(terminate_later)
            unterminated_qubits.difference_update(terminated_by_this_op)

            # unconditionally apply this node to the new dag
            new_dag.apply_operation_back(node.op, node.qargs, node.cargs)
            layers.maybe_start_new_layer(node.qargs)

        # terminate at the end of the circuit, if necessary
        if unterminated_qubits:
            qargs, box = self._new_box(unterminated_qubits, all_qubits)
            box_node = new_dag.apply_operation_back(box, qargs, [])
            layers.add_box(box_node)

        # technically, the above loop constructed a buildable dag. however, it is beneficial to
        # group together all those boxes that can be grouped together to reduce the number of
        # unique boxes in the circuit.
        for layer in filter(lambda layer: len(layer) > 1, layers.layers):
            qubits, box = self._new_box((qubit for box in layer for qubit in box.qargs), all_qubits)
            qubit_map = {qubit: idx for idx, qubit in enumerate(qubits)}
            new_dag.replace_block_with_op(layer, box, qubit_map, cycle_check=False)

        return new_dag
