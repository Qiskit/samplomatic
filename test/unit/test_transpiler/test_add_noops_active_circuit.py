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

"""Test the AddNoopsActiveCircuit pass"""

from qiskit.circuit import Parameter, QuantumCircuit
from qiskit.transpiler import PassManager

from samplomatic.annotations import Twirl
from samplomatic.transpiler.passes.insert_noops import AddNoopsActiveCircuit


def make_circuits():
    theta = Parameter("theta")
    phi = Parameter("phi")
    lam = Parameter("lambda")

    circuit = QuantumCircuit(1)

    expected_circuit = QuantumCircuit(1)

    yield circuit, expected_circuit, "empty_circuit"

    circuit = QuantumCircuit(6)
    with circuit.box([Twirl(dressing="left")]):
        circuit.cx(0, 1)
    with circuit.box([Twirl(dressing="left")]):
        circuit.cx(1, 2)
    with circuit.box([Twirl(dressing="left")]):
        circuit.cx(2, 3)
    with circuit.box([Twirl(dressing="left")]):
        circuit.cx(3, 4)
    with circuit.box([Twirl(dressing="left")]):
        circuit.cx(4, 5)
    with circuit.box([Twirl(dressing="left")]):
        circuit.cx(4, 3)

    expected_circuit = QuantumCircuit(6)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.noop(range(6))
        expected_circuit.cx(0, 1)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.noop(range(6))
        expected_circuit.cx(1, 2)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.noop(range(6))
        expected_circuit.cx(2, 3)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.noop(range(6))
        expected_circuit.cx(3, 4)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.noop(range(6))
        expected_circuit.cx(4, 5)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.noop(range(6))
        expected_circuit.cx(4, 3)

    yield circuit, expected_circuit, "each_gate_in_a_separate_box"

    circuit = QuantumCircuit(7)
    with circuit.box([Twirl(dressing="left")]):
        circuit.cx(0, 1)
    with circuit.box([Twirl(dressing="left")]):
        circuit.cx(1, 2)
    with circuit.box([Twirl(dressing="left")]):
        circuit.cx(2, 3)
    with circuit.box([Twirl(dressing="left")]):
        circuit.cx(3, 4)
    with circuit.box([Twirl(dressing="left")]):
        circuit.cx(4, 5)
    with circuit.box([Twirl(dressing="left")]):
        circuit.cx(4, 3)
    with circuit.box([Twirl(dressing="right")]):
        circuit.noop(range(6))

    expected_circuit = QuantumCircuit(7)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.noop(range(6))
        expected_circuit.cx(0, 1)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.noop(range(6))
        expected_circuit.cx(1, 2)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.noop(range(6))
        expected_circuit.cx(2, 3)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.noop(range(6))
        expected_circuit.cx(3, 4)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.noop(range(6))
        expected_circuit.cx(4, 5)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.noop(range(6))
        expected_circuit.cx(4, 3)
    with expected_circuit.box([Twirl(dressing="right")]):
        expected_circuit.noop(range(6))

    yield circuit, expected_circuit, "terminal_box"

    circuit = QuantumCircuit(6)
    with circuit.box([Twirl(dressing="left")]):
        circuit.cx(4, 3)
        circuit.rz(phi, 1)
        circuit.y(1)
        circuit.cx(1, 2)
    with circuit.box([Twirl(dressing="left")]):
        circuit.x(0)
        circuit.rx(theta, 0)
        circuit.z(0)
        circuit.ecr(0, 1)
    with circuit.box([Twirl(dressing="right")]):
        circuit.sx(3)
        circuit.y(1)
        circuit.noop(range(5))
    circuit.rz(lam, 5)
    circuit.sx(5)

    expected_circuit = QuantumCircuit(6)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.cx(4, 3)
        expected_circuit.rz(phi, 1)
        expected_circuit.y(1)
        expected_circuit.cx(1, 2)
        expected_circuit.noop(range(5))
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.x(0)
        expected_circuit.rx(theta, 0)
        expected_circuit.z(0)
        expected_circuit.ecr(0, 1)
        expected_circuit.noop(range(5))
    with expected_circuit.box([Twirl(dressing="right")]):
        expected_circuit.sx(3)
        expected_circuit.y(1)
        expected_circuit.noop(range(5))
    expected_circuit.rz(lam, 5)
    expected_circuit.sx(5)

    yield circuit, expected_circuit, "boxes_w_1q_2q_gates"

    circuit = QuantumCircuit(6, 1)
    with circuit.box([Twirl(dressing="left")]):
        circuit.cx(4, 3)
        circuit.rz(phi, 1)
        circuit.y(1)
        circuit.cx(1, 2)
        circuit.measure(4, 0)
    with circuit.box([Twirl(dressing="left")]):
        circuit.x(0)
        circuit.rx(theta, 0)
        circuit.z(0)
        circuit.ecr(0, 1)
    with circuit.box([Twirl(dressing="right")]):
        circuit.sx(3)
        circuit.y(1)
        circuit.noop(range(4))
    circuit.rz(lam, 5)
    circuit.sx(5)

    expected_circuit = QuantumCircuit(6, 1)
    expected_circuit.rz(lam, 5)
    expected_circuit.sx(5)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.cx(4, 3)
        expected_circuit.rz(phi, 1)
        expected_circuit.y(1)
        expected_circuit.cx(1, 2)
        expected_circuit.measure(4, 0)
        expected_circuit.noop(range(5))
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.x(0)
        expected_circuit.rx(theta, 0)
        expected_circuit.z(0)
        expected_circuit.ecr(0, 1)
        expected_circuit.noop(range(5))
    with expected_circuit.box([Twirl(dressing="right")]):
        expected_circuit.sx(3)
        expected_circuit.y(1)
        expected_circuit.noop(range(5))

    yield circuit, expected_circuit, "boxes_w_1q_2q_gates_measures"


def pytest_generate_tests(metafunc):
    if "circuits_to_compare" in metafunc.fixturenames:
        circuits_to_compare = [*make_circuits()]
        real_expected_circ_and_args = [(test[0], test[1]) for test in circuits_to_compare]
        descriptions = [test[2] for test in circuits_to_compare]
        metafunc.parametrize("circuits_to_compare", real_expected_circ_and_args, ids=descriptions)


def test_transpiled_circuits_match_expected(circuits_to_compare):
    """Test AddNoopsActiveCircuit pass.

    Applies modified transpiler's box pass to ``circuits_to_compare[0]`` and compares the resulting
    circuit to the circuit extracted from ``circuits_to_compare[1]``. The main goal of these tests
    is to verify the qubits covered by each box in the transpiled circuit are accurate.

    Args:
        circuits_to_compare: A tuple containing a ``(circuit, expected_circuit)`` batch.
    """
    circuit, expected_circuit = circuits_to_compare
    pm = PassManager(passes=[AddNoopsActiveCircuit()])
    transpiled_circuit = pm.run(circuit)

    assert transpiled_circuit == expected_circuit
