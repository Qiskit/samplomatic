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

"""Tests for BoxKey"""

from copy import deepcopy
from itertools import combinations

import pytest
from qiskit.circuit import BoxOp, CircuitInstruction, Parameter, QuantumCircuit, QuantumRegister
from qiskit.circuit.library import CXGate

from samplomatic.annotations import InjectNoise, Twirl
from samplomatic.utils import BoxKey


def make_instructions_with_different_specs():
    """Generate instructions that are expected to have different box keys."""
    body = QuantumCircuit(2)
    body.rz(Parameter("theta"), 0)
    body.cx(0, 1)
    yield CircuitInstruction(BoxOp(body), body.qubits)

    body = QuantumCircuit(2)
    body.rz(Parameter("phi"), 0)
    body.cx(0, 1)
    yield CircuitInstruction(BoxOp(body), body.qubits)

    body = QuantumCircuit(2)
    body.rz(0.1, 0)
    body.cx(0, 1)
    yield CircuitInstruction(BoxOp(body), body.qubits)

    body = QuantumCircuit(2)
    body.rz(0.1, 0)
    body.cx(0, 1)
    body.cx(0, 1)
    body.cx(0, 1)
    yield CircuitInstruction(BoxOp(body), body.qubits)

    body = QuantumCircuit(2)
    body.rz(0.1, 0)
    body.cx(1, 0)
    yield CircuitInstruction(BoxOp(body), body.qubits)

    body = QuantumCircuit(QuantumRegister(2, "register"))
    body.rz(0.1, 0)
    body.cx(0, 1)
    yield CircuitInstruction(BoxOp(body), body.qubits)


def test_constructor():
    """Test the constructor."""
    body = QuantumCircuit(2)
    body.h(0)
    body.cx(0, 1)
    instr = CircuitInstruction(BoxOp(body), body.qubits)

    key = BoxKey(instr)
    assert isinstance(hash(key), int)


def test_constructor_raises():
    """Test that the constructor raises when it is given an instruction without a box."""
    with pytest.raises(ValueError, match="that contains a 'box', found one that contains 'cx'"):
        BoxKey(CXGate())


def test_equivalent_boxes_produce_equal_specs():
    """Test that equivalent boxes produce equal specifications."""
    body1 = QuantumCircuit(2)
    body1.h(0)
    body1.h(1)
    body1.cx(0, 1)
    instr1 = CircuitInstruction(BoxOp(body1), body1.qubits)

    body2 = QuantumCircuit(2)
    body2.h(1)
    body2.h(0)
    body2.cx(0, 1)
    instr2 = CircuitInstruction(BoxOp(body2), body2.qubits)

    key1 = BoxKey(instr1)
    key2 = BoxKey(instr2)

    assert key1 == key2


def test_equal_boxes_produce_equal_keys():
    """Test that equal boxes produce equal keys."""
    body = QuantumCircuit(2)
    body.h(0)
    body.cx(0, 1)
    instr = CircuitInstruction(BoxOp(body), body.qubits)

    key1 = BoxKey(instr)
    key2 = BoxKey(deepcopy(instr))

    assert key1 == key2


def test_different_boxes_produce_different_specs():
    """Test that different boxes produce different specifications."""
    for box1, box2 in combinations(make_instructions_with_different_specs(), 2):
        key1 = BoxKey(box1)
        key2 = BoxKey(box2)

        assert key1 != key2


def test_different_boxes_produce_different_keys():
    """Test that different boxes produce different keys."""
    for instr1, instr2 in combinations(make_instructions_with_different_specs(), 2):
        key1 = BoxKey(instr1)
        key2 = BoxKey(instr2)
        assert key1 != key2


def test_symmetric_gates():
    """Test that symmetric gates are handled correctly."""
    body1 = QuantumCircuit(2)
    body1.h(0)
    body1.h(1)
    body1.cz(0, 1)
    instr1 = CircuitInstruction(BoxOp(body1), body1.qubits)

    body2 = QuantumCircuit(2)
    body2.h(1)
    body2.h(0)
    body2.cz(1, 0)
    instr2 = CircuitInstruction(BoxOp(body2), body2.qubits)

    key1 = BoxKey(instr1)
    key2 = BoxKey(instr2)
    assert key1 == key2


def test_boxes_with_annotations():
    """Test boxes with annotations."""
    body = QuantumCircuit(2)
    body.h(0)
    body.h(1)
    body.cx(0, 1)

    qubits = body.qubits

    instr = CircuitInstruction(BoxOp(body), qubits)
    instr_twirl_inject = CircuitInstruction(
        BoxOp(body, annotations=[Twirl(), InjectNoise("ref")]), qubits
    )
    instr_inject_twirl = CircuitInstruction(
        BoxOp(body, annotations=[InjectNoise("ref"), Twirl()]), qubits
    )

    assert BoxKey(instr) != BoxKey(instr_twirl_inject)
    assert BoxKey(instr) != BoxKey(instr_inject_twirl)
    assert BoxKey(instr_inject_twirl) == BoxKey(instr_twirl_inject)
