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

"""Test the AddTerminalRightDressedBoxes"""

import numpy as np
import pytest
from qiskit.circuit import Parameter, QuantumCircuit
from qiskit.transpiler import PassManager
from qiskit.transpiler.exceptions import TranspilerError

from samplomatic.annotations import BasisTransform, Twirl
from samplomatic.transpiler.passes import AddTerminalRightDressedBoxes


def make_circuits():
    theta = Parameter("theta")

    circuit = QuantumCircuit(1)

    yield circuit, circuit, "empty_circuit"

    for prefix, annotations in [
        ("twirl", [Twirl()]),
        ("basis_transform", [BasisTransform()]),
        ("all", [Twirl(), BasisTransform()]),
    ]:
        circuit = QuantumCircuit(3, 1)
        circuit.cx(0, 1)
        circuit.rx(np.pi / 3, 0)
        circuit.rz(np.pi / 8, 0)
        circuit.h(0)
        circuit.y(2)
        with circuit.box(annotations):
            circuit.x(0)
            circuit.measure(1, 0)  # this acts as a collector
        with circuit.box([Twirl(dressing="right")]):
            circuit.noop(0)
        circuit.measure_all()

        yield circuit, circuit, f"{prefix}_circuit_with_no_uncollected_virtual_gates"

        circuit = QuantumCircuit(3, 2)
        with circuit.box(annotations):
            circuit.cx(0, 1)
            circuit.measure(2, 0)
        circuit.x(0)
        circuit.rz(theta, 1)
        circuit.measure(1, 1)

        expected_circuit = QuantumCircuit(3, 2)
        with expected_circuit.box(annotations):
            expected_circuit.cx(0, 1)
            expected_circuit.measure(2, 0)
        with expected_circuit.box([Twirl(dressing="right")]):
            expected_circuit.x(0)
            expected_circuit.rz(theta, 1)
        expected_circuit.measure(1, 1)

        yield circuit, expected_circuit, f"{prefix}_circuit_with_no_collected_virtual_gates"

        circuit = QuantumCircuit(1, 2)
        with circuit.box(annotations):
            circuit.x(0)
        circuit.measure(0, 0)
        circuit.measure(0, 1)

        expected_circuit = QuantumCircuit(1, 2)
        with expected_circuit.box(annotations):
            expected_circuit.x(0)
        with expected_circuit.box([Twirl(dressing="right")]):
            expected_circuit.noop(0)
        expected_circuit.measure(0, 0)
        expected_circuit.measure(0, 1)

        yield circuit, expected_circuit, f"{prefix}_circuit_with_back_to_back_unboxed_measurements"

        circuit = QuantumCircuit(1, 2)
        with circuit.box(annotations):
            circuit.x(0)
        circuit.z(0)
        circuit.measure(0, 0)
        circuit.y(0)
        circuit.measure(0, 1)

        expected_circuit = QuantumCircuit(1, 2)
        with expected_circuit.box(annotations):
            expected_circuit.x(0)
        with expected_circuit.box([Twirl(dressing="right")]):
            expected_circuit.z(0)
        expected_circuit.measure(0, 0)
        expected_circuit.y(0)
        expected_circuit.measure(0, 1)

        yield (
            circuit,
            expected_circuit,
            f"{prefix}_circuit_with_back_to_back_gates_and_unboxed_measurements",
        )


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
    """Test `AddTerminalRightDressedBoxes`.

    Args:
        circuits_to_compare: A tuple containing a ``(circuit, expected_circuit)`` pair.
    """
    circuit, expected_circuit = circuits_to_compare
    pm = PassManager(passes=[AddTerminalRightDressedBoxes()])
    transpiled_circuit = pm.run(circuit)

    assert transpiled_circuit == expected_circuit


def test_raises_for_unsupported_ops():
    """Test that `AddTerminalRightDressedBoxes` raises when the circuit contains unsupported ops."""
    pm = PassManager(passes=[AddTerminalRightDressedBoxes()])

    circuit = QuantumCircuit(1)
    circuit.prepare_state(1)

    with pytest.raises(TranspilerError, match="``'state_preparation'`` is not supported"):
        pm.run(circuit)

    circuit = QuantumCircuit(2, 3)
    with circuit.box([Twirl()]):
        circuit.x(0)
        circuit.measure(1, 0)
    with circuit.if_test((0, 1)):
        circuit.x(1)

    with pytest.raises(TranspilerError, match="``'if_else'`` is not supported"):
        pm.run(circuit)
