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

"""Test InlineBoxes"""

from qiskit.circuit import QuantumCircuit
from qiskit.transpiler import PassManager

from samplomatic.transpiler.passes import InlineBoxes


def make_circuits():
    circuit = QuantumCircuit(1)

    yield circuit, circuit, "empty_circuit"

    circuit = QuantumCircuit(4, 4)
    circuit.h(1)
    circuit.cx(1, 2)
    circuit.cx(3, 1)
    circuit.cx(2, 0)
    circuit.measure(range(4), range(4))

    yield circuit, circuit, "circuit_without_boxes"

    circuit = QuantumCircuit(4, 4)
    with circuit.box():
        circuit.h(1)
        circuit.cx(1, 2)
    with circuit.box():
        circuit.cx(1, 3)
    with circuit.box():
        circuit.cx(2, 0)
        circuit.measure(range(4), range(4))

    expected_circuit = QuantumCircuit(4, 4)
    expected_circuit.h(1)
    expected_circuit.cx(1, 2)
    expected_circuit.cx(1, 3)
    expected_circuit.cx(2, 0)
    expected_circuit.measure(range(4), range(4))

    yield circuit, expected_circuit, "circuit_with_boxes"

    circuit = QuantumCircuit(4, 4)
    with circuit.box():
        circuit.h(1)
        circuit.cx(1, 2)
    with circuit.box():
        with circuit.box():
            circuit.noop(2)
            with circuit.box():
                circuit.noop(3)
                circuit.cx(1, 3)
    with circuit.box():
        circuit.cx(2, 0)
        circuit.measure(range(4), range(4))

    expected_circuit = QuantumCircuit(4, 4)
    expected_circuit.h(1)
    expected_circuit.cx(1, 2)
    expected_circuit.cx(1, 3)
    expected_circuit.cx(2, 0)
    expected_circuit.measure(range(4), range(4))

    yield circuit, expected_circuit, "circuit_with_nested_boxes"


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


def test_transpiled_circuits_are_correct(circuits_to_compare):
    """Test `InlineBoxes`.

    Args:
        circuits_to_compare: A tuple containing a ``(circuit, expected_circuit)`` pair.
    """
    circuit, expected_circuit = circuits_to_compare
    pm = PassManager(passes=[InlineBoxes()])
    transpiled_circuit = pm.run(circuit)

    assert transpiled_circuit == expected_circuit
