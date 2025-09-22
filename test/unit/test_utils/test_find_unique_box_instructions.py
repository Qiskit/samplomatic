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

"""Tests for `find_unique_box_instructions`"""

from qiskit.circuit import BoxOp, CircuitInstruction, Parameter, QuantumCircuit
from qiskit.circuit.library import CXGate

from samplomatic.annotations import InjectNoise, Twirl
from samplomatic.utils import BoxKey, find_unique_box_instructions, undress_box


def test_undress_boxes_is_true():
    """Test ``find_unique_box_instructions`` when ``undress_boxes`` is ``True``."""
    body = QuantumCircuit(4)
    body.h(0)
    body.cz(0, 1)
    annotations = [Twirl(decomposition="rzrx")]
    instr0 = CircuitInstruction(BoxOp(body, annotations=annotations), body.qubits)

    body = QuantumCircuit(4)
    body.y(0)
    body.t(0)
    body.s(2)
    body.cz(0, 1)
    annotations = [Twirl(decomposition="rzrx")]
    instr1 = CircuitInstruction(BoxOp(body, annotations=annotations), body.qubits)

    body = QuantumCircuit(4)
    body.cz(1, 0)  # qubits in reverse order
    body.rz(Parameter("phi"), 0)
    annotations = [Twirl(dressing="right")]
    instr2 = CircuitInstruction(BoxOp(body, annotations=annotations), body.qubits)

    body = QuantumCircuit(2)
    body.cz(0, 1)
    body.rz(Parameter("phi"), 0)
    annotations = [Twirl()]
    instr3 = CircuitInstruction(BoxOp(body, annotations=annotations), body.qubits)

    unique_instructions = find_unique_box_instructions([instr0, instr1, instr2, instr3])
    assert len(unique_instructions) == 3

    expected_instr0 = CircuitInstruction(undress_box(instr0.operation), instr0.qubits)
    expected_instr0.operation.annotations = [Twirl(decomposition="rzrx")]
    expected_instr1 = CircuitInstruction(undress_box(instr2.operation), instr2.qubits)
    expected_instr1.operation.annotations = [Twirl(dressing="right")]
    expected_instr2 = CircuitInstruction(undress_box(instr3.operation), instr3.qubits)
    expected_instr2.operation.annotations = [Twirl()]

    assert BoxKey(unique_instructions[0]) == BoxKey(expected_instr0)
    assert BoxKey(unique_instructions[1]) == BoxKey(expected_instr1)
    assert BoxKey(unique_instructions[2]) == BoxKey(expected_instr2)


def test_undress_boxes_is_false():
    """Test ``find_unique_box_instructions`` when ``undress_boxes`` is ``False``."""
    body = QuantumCircuit(4)
    body.h(0)
    body.cz(0, 1)
    annotations = [Twirl(decomposition="rzrx")]
    instr0 = CircuitInstruction(BoxOp(body, annotations=annotations), body.qubits)

    body = QuantumCircuit(4)
    body.y(0)
    body.t(0)
    body.s(2)
    body.cz(0, 1)
    annotations = [Twirl(decomposition="rzrx")]
    instr1 = CircuitInstruction(BoxOp(body, annotations=annotations), body.qubits)

    body = QuantumCircuit(4)
    body.cz(1, 0)  # qubits in reverse order
    body.rz(Parameter("phi"), 0)
    annotations = [Twirl(dressing="right")]
    instr2 = CircuitInstruction(BoxOp(body, annotations=annotations), body.qubits)

    body = QuantumCircuit(2)
    body.cz(0, 1)
    body.rz(Parameter("phi"), 0)
    annotations = [Twirl()]
    instr3 = CircuitInstruction(BoxOp(body, annotations=annotations), body.qubits)

    instructions = [instr0, instr1, instr2, instr3]
    unique_instructions = find_unique_box_instructions(
        instructions,
        undress_boxes=False,
        normalize_annotations=lambda _: [],
    )
    assert len(unique_instructions) == 4

    for instr, unique_instr in zip(instructions, unique_instructions):
        expected_instr = instr
        expected_instr.operation.annotations = []
        assert BoxKey(expected_instr) == BoxKey(unique_instr)


def test_normalize_annotations():
    """Test the ``normalize_annotations`` argument of ``find_unique_box_instructions``."""
    body = QuantumCircuit(4)
    body.h(0)
    body.cz(0, 1)
    annotations = [Twirl(decomposition="rzrx"), InjectNoise("ref", "mod_ref")]
    instr0 = CircuitInstruction(BoxOp(body, annotations=annotations), body.qubits)

    body = QuantumCircuit(4)
    body.y(0)
    body.t(0)
    body.s(2)
    body.cz(0, 1)
    annotations = [Twirl(decomposition="rzrx"), InjectNoise("ref", "another_modifier_ref")]
    instr1 = CircuitInstruction(BoxOp(body, annotations=annotations), body.qubits)

    body = QuantumCircuit(4)
    body.rz(Parameter("phi"), 0)
    body.cz(1, 0)
    annotations = [Twirl()]
    instr2 = CircuitInstruction(BoxOp(body, annotations=annotations), body.qubits)

    instructions = [instr0, instr1, instr2]

    unique_instructions = find_unique_box_instructions(
        instructions,
        normalize_annotations=lambda annotations: [
            Twirl(dressing=annot.dressing) for annot in annotations if isinstance(annot, Twirl)
        ],
    )
    assert len(unique_instructions) == 1
    assert unique_instructions[0].operation.annotations == [Twirl()]

    unique_instructions = find_unique_box_instructions(
        instructions,
        normalize_annotations=lambda annotations: [
            Twirl(decomposition=annot.decomposition)
            for annot in annotations
            if isinstance(annot, Twirl)
        ],
    )
    assert len(unique_instructions) == 2
    assert unique_instructions[0].operation.annotations == [Twirl(decomposition="rzrx")]
    assert unique_instructions[1].operation.annotations == [Twirl()]

    unique_instructions = find_unique_box_instructions(
        instructions,
        normalize_annotations=lambda annotations: [
            InjectNoise(annot.ref) for annot in annotations if isinstance(annot, InjectNoise)
        ],
    )
    assert len(unique_instructions) == 2
    assert unique_instructions[0].operation.annotations == [InjectNoise("ref")]
    assert unique_instructions[1].operation.annotations == []

    unique_instructions = find_unique_box_instructions(
        instructions,
        normalize_annotations=lambda annotations: [
            InjectNoise(annot.ref, annot.modifier_ref)
            for annot in annotations
            if isinstance(annot, InjectNoise)
        ],
    )
    assert len(unique_instructions) == 3
    assert unique_instructions[0].operation.annotations == [InjectNoise("ref", "mod_ref")]
    assert unique_instructions[1].operation.annotations == [
        InjectNoise("ref", "another_modifier_ref")
    ]
    assert unique_instructions[2].operation.annotations == []


def test_annotation_handling():
    """Test that ``find_unique_box_instructions`` does not modify annotations in-place."""
    inject_noise = InjectNoise("ref", "modifier_ref")
    circuit = QuantumCircuit(2)
    with circuit.box(annotations=[inject_noise]):
        circuit.cx(0, 1)

    find_unique_box_instructions(circuit)
    inject_noise_after = circuit[0].operation.annotations[0]
    assert inject_noise == inject_noise_after


def test_continue():
    """Test that ``find_unique_box_instructions`` continues if it finds non-boxes."""
    assert find_unique_box_instructions([CXGate()]) == []
