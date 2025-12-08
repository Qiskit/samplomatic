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

"""Test the AddNoops pass"""

import pytest
from qiskit.circuit import Parameter, QuantumCircuit, QuantumRegister
from qiskit.transpiler import PassManager
from qiskit.transpiler.exceptions import TranspilerError

from samplomatic.annotations import Twirl
from samplomatic.transpiler.passes.insert_noops import AddNoops


def make_circuits():
    theta = Parameter("theta")

    circuit = QuantumCircuit(1)

    expected_circuit = QuantumCircuit(1)

    yield circuit, {0}, expected_circuit, "empty_circuit"

    circuit = QuantumCircuit(4)
    with circuit.box([Twirl(dressing="left")]):
        circuit.cz(0, 1)
    with circuit.box([Twirl(dressing="right")]):
        circuit.noop(0, 1)

    for qubits, label in [
        [range(2), "complete_overlap"],
        [range(1, 3), "partial_overlap"],
        [range(2, 4), "no_overlap"],
    ]:
        expected_circuit = QuantumCircuit(4)
        with expected_circuit.box([Twirl(dressing="left")]):
            expected_circuit.cz(0, 1)
            expected_circuit.noop(qubits)
        with expected_circuit.box([Twirl(dressing="right")]):
            expected_circuit.noop(0, 1)
            expected_circuit.noop(qubits)
        yield circuit, set(qubits), expected_circuit, label

    circuit = QuantumCircuit(6)
    circuit.x(0)
    circuit.rx(theta, 0)
    with circuit.box([Twirl(dressing="left")]):
        circuit.cx(1, 2)
        circuit.cx(4, 3)
    with circuit.box([Twirl(dressing="right")]):
        circuit.z(1)
        circuit.noop(range(1, 5))

    for qubits, label in [
        [range(1), "one_qubit"],
        [range(2), "two_qubits"],
        [range(len(circuit.qubits)), "all_qubits"],
    ]:
        expected_circuit = QuantumCircuit(6)
        expected_circuit.x(0)
        expected_circuit.rx(theta, 0)
        with expected_circuit.box([Twirl(dressing="left")]):
            expected_circuit.cx(1, 2)
            expected_circuit.cx(4, 3)
            expected_circuit.noop(qubits)
        with expected_circuit.box([Twirl(dressing="right")]):
            expected_circuit.z(1)
            expected_circuit.noop(range(1, 5))
            expected_circuit.noop(qubits)
        yield circuit, set(qubits), expected_circuit, label

    circuit = QuantumCircuit(4, 2)
    with circuit.box([Twirl(dressing="left")]):
        circuit.cx(0, 1)
    with circuit.box([Twirl(dressing="left")]):
        circuit.x(0)
    circuit.t(1)
    circuit.measure(1, 0)
    circuit.measure(2, 0)
    with circuit.box([Twirl(dressing="left")]):
        circuit.cx(2, 3)
    circuit.barrier()
    circuit.measure(1, 0)
    with circuit.box([Twirl(dressing="left")]):
        circuit.cx(0, 1)
    circuit.measure(2, 1)

    expected_circuit = QuantumCircuit(4, 2)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.cx(0, 1)
        expected_circuit.noop(3)
    expected_circuit.t(1)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.x(0)
        expected_circuit.noop(3)
    expected_circuit.measure(1, 0)
    expected_circuit.measure(2, 0)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.cx(2, 3)
    expected_circuit.barrier()
    expected_circuit.measure(1, 0)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.cx(0, 1)
        expected_circuit.noop(3)
    expected_circuit.measure(2, 1)

    yield circuit, {circuit.qubits[3]}, expected_circuit, "circuit_with_measurements"


def pytest_generate_tests(metafunc):
    if "circuits_to_compare" in metafunc.fixturenames:
        circuits_to_compare = [*make_circuits()]
        real_expected_circ_and_args = [(test[0], test[1], test[2]) for test in circuits_to_compare]
        descriptions = [test[3] for test in circuits_to_compare]
        metafunc.parametrize("circuits_to_compare", real_expected_circ_and_args, ids=descriptions)


def test_transpiled_circuits_have_correct_boxops(circuits_to_compare):
    """Test AddNoops pass.

    Applies modified transpiler's box pass with the argument, ``circuits_to_compare[1]``,
    determining which qubits to expand boxes to. The function acts on ``circuits_to_compare[0]``
    and compares the resulting circuit to the circuit extracted from ``circuits_to_compare[2]``.
    The main goal of these tests is to verify the qubits covered by each box in the transpiled
    circuit are accurate.

    Args:
        circuits_to_compare: A tuple containing a ``(circuit, qubit_set, expected_circuit)`` batch.
    """
    circuit, selected_qubits, expected_circuit = circuits_to_compare
    pm = PassManager(passes=[AddNoops(selected_qubits)])
    transpiled_circuit = pm.run(circuit)

    assert transpiled_circuit == expected_circuit


def test_add_noops_raises():
    """Test that `AddNoops()` raises."""
    circuit = QuantumCircuit(QuantumRegister(1, "qreg"))
    pm = PassManager(AddNoops({2}))
    with pytest.raises(
        TranspilerError, match="Not all of the specified qubit(s) are in this circuit."
    ):
        pm.run(circuit)

    circuit2 = QuantumCircuit(1)
    pm2 = PassManager(AddNoops({circuit.qubits[0]}))
    with pytest.raises(
        TranspilerError, match="Not all of the specified qubit(s) are in this circuit."
    ):
        pm2.run(circuit2)
