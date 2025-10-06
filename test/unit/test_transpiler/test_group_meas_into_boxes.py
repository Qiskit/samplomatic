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

"""Test the GroupMeasIntoBoxes"""

import pytest
from qiskit.circuit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.transpiler import PassManager
from qiskit.transpiler.exceptions import TranspilerError

from samplomatic import BasisTransform, Twirl
from samplomatic.transpiler.passes import GroupMeasIntoBoxes
from samplomatic.utils import get_annotation


def make_circuits():
    qreg_a = QuantumRegister(4, "qreg_a")
    creg_a = ClassicalRegister(2, "creg_a")
    creg_b = ClassicalRegister(3, "creg_b")

    circuit = QuantumCircuit(1)

    expected_circuit = QuantumCircuit(1)

    yield circuit, expected_circuit, "empty_circuit"

    circuit = QuantumCircuit(2, 2)
    circuit.sdg(0)
    circuit.x(0)
    circuit.z(0)
    circuit.y(1)
    circuit.measure(0, 0)
    circuit.measure(1, 1)
    circuit.t(0)
    circuit.h(0)
    circuit.sx(1)

    expected_circuit = QuantumCircuit(2, 2)
    with expected_circuit.box([Twirl()]):
        expected_circuit.y(1)
        expected_circuit.measure(1, 1)
        expected_circuit.sdg(0)
        expected_circuit.x(0)
        expected_circuit.z(0)
        expected_circuit.measure(0, 0)
    expected_circuit.t(0)
    expected_circuit.h(0)
    expected_circuit.sx(1)

    yield circuit, expected_circuit, "circuit_with_1qubit_gates_and_measurements"

    circuit = QuantumCircuit(qreg_a, creg_a, creg_b)
    circuit.sdg(0)
    circuit.x(0)
    circuit.z(0)
    circuit.y(1)
    circuit.measure(0, 0)
    circuit.measure(1, 1)
    circuit.t(0)
    circuit.h(0)
    circuit.sx(1)

    expected_circuit = QuantumCircuit(qreg_a, creg_a, creg_b)
    with expected_circuit.box([Twirl()]):
        expected_circuit.y(1)
        expected_circuit.measure(1, 1)
        expected_circuit.sdg(0)
        expected_circuit.x(0)
        expected_circuit.z(0)
        expected_circuit.measure(0, 0)
    expected_circuit.t(0)
    expected_circuit.h(0)
    expected_circuit.sx(1)

    yield circuit, expected_circuit, "circuit_with_multiple_cregs"

    circuit = QuantumCircuit(3, 3)
    circuit.sdg(0)
    circuit.barrier(0)
    circuit.x(0)
    circuit.z(0)
    circuit.y(1)
    circuit.barrier(1)
    circuit.measure(0, 0)
    circuit.barrier(0, 1)
    circuit.measure(1, 1)
    circuit.measure(2, 2)

    expected_circuit = QuantumCircuit(3, 3)
    expected_circuit.sdg(0)
    expected_circuit.barrier(0)
    expected_circuit.y(1)
    expected_circuit.barrier(1)
    with expected_circuit.box([Twirl()]):
        expected_circuit.measure(2, 2)
        expected_circuit.x(0)
        expected_circuit.z(0)
        expected_circuit.measure(0, 0)
    expected_circuit.barrier(0, 1)
    with expected_circuit.box([Twirl()]):
        expected_circuit.measure(1, 1)

    yield circuit, expected_circuit, "circuit_with_barriers_as_delimiters"

    circuit = QuantumCircuit(3, 3)
    circuit.sdg(0)
    with circuit.box():
        circuit.noop(0)
    circuit.x(0)
    circuit.z(0)
    circuit.y(1)
    with circuit.box():
        circuit.noop(1)
    circuit.measure(0, 0)
    with circuit.box():
        circuit.noop(0, 1)
    circuit.measure(1, 1)
    circuit.measure(2, 2)

    expected_circuit = QuantumCircuit(3, 3)
    expected_circuit.sdg(0)
    with expected_circuit.box():
        expected_circuit.noop(0)
    expected_circuit.y(1)
    with expected_circuit.box():
        expected_circuit.noop(1)
    with expected_circuit.box([Twirl()]):
        expected_circuit.measure(2, 2)
        expected_circuit.x(0)
        expected_circuit.z(0)
        expected_circuit.measure(0, 0)
    with expected_circuit.box():
        expected_circuit.noop(0, 1)
    with expected_circuit.box([Twirl()]):
        expected_circuit.measure(1, 1)

    yield circuit, expected_circuit, "circuit_with_boxes_as_delimiters"

    circuit = QuantumCircuit(3, 3)
    circuit.sdg(0)
    circuit.cz(0, 1)
    circuit.x(0)
    circuit.z(0)
    circuit.y(1)
    circuit.cx(1, 2)
    circuit.measure(0, 0)
    circuit.t(1)
    circuit.ecr(0, 2)
    circuit.measure(1, 1)
    circuit.measure(2, 2)

    expected_circuit = QuantumCircuit(3, 3)
    expected_circuit.sdg(0)
    expected_circuit.cz(0, 1)
    expected_circuit.y(1)
    expected_circuit.cx(1, 2)
    with expected_circuit.box([Twirl()]):
        expected_circuit.t(1)
        expected_circuit.measure(1, 1)
        expected_circuit.x(0)
        expected_circuit.z(0)
        expected_circuit.measure(0, 0)
    expected_circuit.ecr(0, 2)
    with expected_circuit.box([Twirl()]):
        expected_circuit.measure(2, 2)

    yield circuit, expected_circuit, "circuit_with_2q_gates_as_delimiters"


def pytest_generate_tests(metafunc):
    if "circuit" in metafunc.fixturenames:
        circuits_and_descriptions = [*make_circuits()]
        circuits = [test[0] for test in circuits_and_descriptions]
        descriptions = [test[2] for test in circuits_and_descriptions]
        metafunc.parametrize("circuit", circuits, ids=descriptions)
    if "circuits_to_compare" in metafunc.fixturenames:
        circuits_to_compare = [*make_circuits()]
        real_and_expected = [(test[0], test[1]) for test in circuits_to_compare]
        descriptions = [test[2] for test in circuits_to_compare]
        metafunc.parametrize("circuits_to_compare", real_and_expected, ids=descriptions)


def test_transpiled_circuits_have_correct_boxops(circuits_to_compare):
    """Test `GroupMeasIntoBoxes`.

    Args:
        circuits_to_compare: A tuple containing a ``(circuit, expected_circuit)`` pair.
    """
    circuit, expected_circuit = circuits_to_compare
    pm = PassManager(passes=[GroupMeasIntoBoxes()])
    transpiled_circuit = pm.run(circuit)

    assert transpiled_circuit == expected_circuit


@pytest.mark.parametrize("annotations", ["twirl", "basis_transform", "all"])
def test_annotations(annotations):
    """Test that `GroupMeasIntoBoxes` attaches the correct annotations."""
    circuit = QuantumCircuit(1, 1)
    circuit.measure(0, 0)

    pm = PassManager(passes=[GroupMeasIntoBoxes(annotations, "ciao")])
    box = pm.run(circuit).data[0].operation
    twirl = get_annotation(box, Twirl)
    basis_transform = get_annotation(box, BasisTransform)

    assert (twirl is not None) == (annotations in ["twirl", "all"])
    assert (basis_transform is not None) == (annotations in ["basis_transform", "all"])

    if basis_transform:
        assert basis_transform.mode == "measure"
        assert basis_transform.ref.startswith("ciao")


def test_annotations_raise():
    """Test that `GroupMeasIntoBoxes` raises for incorrect annotations."""
    with pytest.raises(ValueError, match="none is not a valid input"):
        GroupMeasIntoBoxes("none")


def test_raises_when_measurements_overwrite_clbit():
    """Test that `GroupMeasIntoBoxes` raises when measurements overwrite a clbit."""
    pm = PassManager(passes=[GroupMeasIntoBoxes()])

    circuit = QuantumCircuit(3, 3)
    circuit.measure(0, 0)
    circuit.measure(1, 1)
    circuit.measure(2, 2)
    circuit.measure(0, 0)
    circuit.measure(1, 0)

    with pytest.raises(TranspilerError, match="more than one measurement"):
        pm.run(circuit)


def test_raises_for_unsupported_ops():
    """Test that `GroupMeasIntoBoxes` raises when the circuit contains unsupported ops."""
    pm = PassManager(passes=[GroupMeasIntoBoxes()])

    circuit = QuantumCircuit(1)
    circuit.prepare_state(1)

    with pytest.raises(TranspilerError, match="``'state_preparation'`` is not supported"):
        pm.run(circuit)

    circuit = QuantumCircuit(2, 3)
    with circuit.box([Twirl(dressing="left")]):
        circuit.x(0)
        circuit.measure(1, 0)
    with circuit.if_test((0, 1)):
        circuit.x(1)

    with pytest.raises(TranspilerError, match="``'if_else'`` is not supported"):
        pm.run(circuit)
