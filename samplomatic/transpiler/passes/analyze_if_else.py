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

"""Helper functions that analyze if-else instructions and convert them to twirlable form"""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Literal

from qiskit.circuit import IfElseOp, QuantumCircuit

from ...aliases import CircuitInstruction

IGNORED_OPS: frozenset[str] = frozenset(["barrier", "delay", "id"])


@dataclass
class IfElseTwirlableForm:
    """The twirlable form of an ``IfElseOp``."""

    instr: CircuitInstruction | None
    """The ``IfElseOp`` which is twirlable. If the original op is twirlable as is set to `None`."""

    additional_1q_ops: list[CircuitInstruction] = field(default_factory=list)
    """List of 1Q gates which need to be added to the circuit (before or after the conditional
    depending on the dressing)."""


class BranchSpecs:
    """A helper class to store the composition of a branch."""

    def __init__(self):
        self.leading_1q = defaultdict(list)
        self.trailing_1q = defaultdict(list)
        self.is_2q = defaultdict(lambda: False)


def analyze_if_else_instruction(
    instr: CircuitInstruction,
) -> tuple[IfElseTwirlableForm | None, IfElseTwirlableForm | None]:
    """A helper function which analyzes ``IfElseOp`` and converts it into a twirlable form.

    Args:
        instr: The ``IfElseOp`` to analyze.

    Returns: A two-tuple ``IfElseTwirlableForm | None`` with the twirlable form of the instruction
        for left\right dressing (first\second element respectively). The values are set to
        ``None`` if no twirlable form exists.
    """
    if_spec = analyze_branch(instr.operation.params[0])
    # TODO: Account for empty else branch
    else_spec = analyze_branch(instr.operation.params[1])
    left = make_twirlable(instr, if_spec, else_spec, "left")
    right = make_twirlable(instr, if_spec, else_spec, "right")
    return (left, right)


def make_twirlable(
    original_if_else: CircuitInstruction,
    if_spec: BranchSpecs,
    else_spec: BranchSpecs,
    dressing=Literal["left", "right"],
):
    """Create a twirlable form for a given dressing"""
    if dressing == "left":
        if_branch_1q = if_spec.trailing_1q
        else_branch_1q = else_spec.trailing_1q
    else:
        if_branch_1q = if_spec.leading_1q
        else_branch_1q = else_spec.leading_1q

    qubits = original_if_else.qubits

    ops_to_move = find_ops_to_move(
        qubits,
        {qubit: if_branch_1q[qubit] if if_spec.is_2q[qubit] else [] for qubit in qubits},
        {qubit: else_branch_1q[qubit] if else_spec.is_2q[qubit] else [] for qubit in qubits},
    )
    if isinstance(ops_to_move, tuple):
        from_if, from_else = ops_to_move
        additional_1q_gates = []
        if len(from_if) == 0 and len(from_else) == 0:
            # Twirlable as is.
            return IfElseTwirlableForm(instr=None)
        else:
            # TODO: The appending of inversed instructions here is wrong for right dressing.
            # with right dressing we remove the gate on the left of the conditional, so
            # the inversed instruction needs to go into the left side of the branch, and not its
            # right.
            new_if = original_if_else.operation.params[0].copy_empty_like()
            for idx, instr in enumerate(original_if_else.operation.params[0]):
                if idx not in from_if:  # a bit inefficient on a list, but shouldn't be a large one
                    new_if.append(instr)
            for idx in from_else:
                instr = original_if_else.operation.params[1][idx]
                new_if.append(
                    CircuitInstruction(instr.operation.inverse(), instr.qubits, instr.clbits)
                )
                additional_1q_gates.append(instr)

            new_else = original_if_else.operation.params[1].copy_empty_like()
            for idx, instr in enumerate(original_if_else.operation.params[1]):
                if (
                    idx not in from_else
                ):  # a bit inefficient on a list, but shouldn't be a large one
                    new_else.append(instr)
            for idx in from_if:
                instr = original_if_else.operation.params[0][idx]
                new_else.append(
                    CircuitInstruction(instr.operation.inverse(), instr.qubits, instr.clbits)
                )
                additional_1q_gates.append(instr)

            new_if_else_op = IfElseOp(
                original_if_else.operation.condition,
                new_if,
                new_else,
                original_if_else.operation.label,
            )
            return IfElseTwirlableForm(
                CircuitInstruction(
                    operation=new_if_else_op,
                    qubits=original_if_else.qubits,
                    clbits=original_if_else.clbits,
                ),
                additional_1q_gates,
            )
    else:
        # Not twirlable
        return None


def find_ops_to_move(qubits, if_branch_1q, else_branch_1q):
    """Examine the 1Q gates on the emitter side of the ``IfElseOp`` and determine if they
    can be moved to create a twirlable form."""
    if any(if_branch_1q[qubit] and else_branch_1q[qubit] for qubit in qubits):
        # At lease one qubit has on the emitter side 1Q gates before a 2Q gate, on both
        # branches of the IfElseOp, so it cannot be converted to a twirlable form.
        return None

    return (
        [idx for idxs in if_branch_1q.values() for idx in idxs],
        [idx for idxs in else_branch_1q.values() for idx in idxs],
    )


def analyze_branch(circuit: QuantumCircuit):
    qubit_status = defaultdict(lambda: "leading")
    spec = BranchSpecs()
    for idx, instr in enumerate(circuit):
        if instr.operation.name in IGNORED_OPS:
            continue
        if instr.operation.num_qubits == 1:
            if qubit_status[instr.qubits[0]] == "leading":
                spec.leading_1q[instr.qubits[0]].append(idx)
            else:
                qubit_status[instr.qubits[0]] = "trailing"
                spec.trailing_1q[instr.qubits[0]].append(idx)
        else:
            if any(qubit_status[qubit] == "trailing" for qubit in instr.qubits):
                # 1Q-2Q-1Q and another 2Q. Not twirlable.
                return None
            for qubit in instr.qubits:
                qubit_status[qubit] = "2q"
                spec.is_2q[qubit] = True

    return spec
