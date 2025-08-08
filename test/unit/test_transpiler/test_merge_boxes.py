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

"""Test the GroupGatesIntoBoxes"""

from qiskit.circuit import Parameter, QuantumCircuit, QuantumRegister
from qiskit.transpiler import PassManager

from samplomatic.annotations import Twirl
from samplomatic.transpiler.passes import MergeBoxes


def make_circuits():
    qreg = QuantumRegister(5)
    p = Parameter("p")

    circuit = QuantumCircuit(qreg)
    with circuit.box([Twirl(dressing="left")]):
        circuit.rz(p, 0)
        circuit.noop(range(5))
    with circuit.box([Twirl(dressing="left")]):
        circuit.rz(p, 0)
        circuit.noop(range(5))
    with circuit.box([Twirl(dressing="left")]):
        circuit.noop(0)
        circuit.rz(2 * p, 1)
        circuit.rz(3 * p, 2)
        circuit.rz(4 * p, 3)
        circuit.rz(5 * p, 4)
        circuit.cx(1, 2)
        circuit.cx(3, 4)
    with circuit.box([Twirl(dressing="left")]):
        circuit.noop(0)
        circuit.rz(2 * p, 1)
        circuit.rz(3 * p, 2)
        circuit.rz(4 * p, 3)
        circuit.rz(5 * p, 4)
        circuit.cx(1, 2)
        circuit.cx(3, 4)
    circuit.barrier()

    expected_circuit = QuantumCircuit(qreg)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.rz(p, 0)
        expected_circuit.rz(p, 0)
        expected_circuit.rz(2 * p, 1)
        expected_circuit.rz(3 * p, 2)
        expected_circuit.rz(4 * p, 3)
        expected_circuit.rz(5 * p, 4)
        expected_circuit.cx(1, 2)
        expected_circuit.cx(3, 4)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.noop(0)
        expected_circuit.rz(2 * p, 1)
        expected_circuit.rz(3 * p, 2)
        expected_circuit.rz(4 * p, 3)
        expected_circuit.rz(5 * p, 4)
        expected_circuit.cx(1, 2)
        expected_circuit.cx(3, 4)
    expected_circuit.barrier()

    yield circuit, expected_circuit, "rzs_to_next_box"

    circuit = QuantumCircuit(qreg)
    with circuit.box([Twirl(dressing="left")]):
        circuit.rz(p, 0)
        circuit.rz(p, 0)
        circuit.noop(range(5))
    circuit.barrier()
    with circuit.box([Twirl(dressing="left")]):
        circuit.noop(0)
        circuit.rz(2 * p, 1)
        circuit.rz(3 * p, 2)
        circuit.rz(4 * p, 3)
        circuit.rz(5 * p, 4)
        circuit.cx(1, 2)
        circuit.cx(3, 4)
    with circuit.box([Twirl(dressing="left")]):
        circuit.noop(0)
        circuit.rz(2 * p, 1)
        circuit.rz(3 * p, 2)
        circuit.rz(4 * p, 3)
        circuit.rz(5 * p, 4)
        circuit.cx(1, 2)
        circuit.cx(3, 4)

    expected_circuit = QuantumCircuit(qreg)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.rz(p, 0)
        expected_circuit.rz(p, 0)
        expected_circuit.noop(range(5))
    expected_circuit.barrier()
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.noop(0)
        expected_circuit.rz(2 * p, 1)
        expected_circuit.rz(3 * p, 2)
        expected_circuit.rz(4 * p, 3)
        expected_circuit.rz(5 * p, 4)
        expected_circuit.cx(1, 2)
        expected_circuit.cx(3, 4)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.noop(0)
        expected_circuit.rz(2 * p, 1)
        expected_circuit.rz(3 * p, 2)
        expected_circuit.rz(4 * p, 3)
        expected_circuit.rz(5 * p, 4)
        expected_circuit.cx(1, 2)
        expected_circuit.cx(3, 4)

    yield circuit, expected_circuit, "no_merge"

    circuit = QuantumCircuit(6, 4)
    with circuit.box([Twirl(dressing="left")]):
        circuit.x(2)
    with circuit.box([Twirl(dressing="left")]):
        circuit.measure(0, 0)
        circuit.measure(1, 1)
        circuit.measure(3, 2)
        circuit.measure(4, 3)
        circuit.noop(2)
    circuit.barrier(1, 2)
    circuit.rz(p, 5)

    expected_circuit = QuantumCircuit(6, 4)
    expected_circuit.rz(p, 5)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.x(2)
        expected_circuit.measure(0, 0)
        expected_circuit.measure(1, 1)
        expected_circuit.measure(3, 2)
        expected_circuit.measure(4, 3)
    expected_circuit.barrier(1, 2)

    yield circuit, expected_circuit, "merge_with_measure_box"

    circuit = QuantumCircuit(6)
    with circuit.box([Twirl(dressing="left")]):
        circuit.x(0)
        circuit.x(1)
        circuit.x(2)
    circuit.barrier(0, 1, 2)
    with circuit.box([Twirl(dressing="left")]):
        circuit.x(3)
        circuit.x(4)
    circuit.barrier(3, 4)
    circuit.rz(p, 5)

    expected_circuit = QuantumCircuit(6)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.x(0)
        expected_circuit.x(1)
        expected_circuit.x(2)
        expected_circuit.x(3)
        expected_circuit.x(4)
    expected_circuit.barrier(0, 1, 2)
    expected_circuit.barrier(3, 4)
    expected_circuit.rz(p, 5)

    yield circuit, expected_circuit, "parallel_barriers"

    circuit = QuantumCircuit(6)
    with circuit.box([Twirl(dressing="left")]):
        circuit.x(2)
    with circuit.box([Twirl(dressing="left")]):
        circuit.cx(0, 1)
        circuit.cx(3, 4)
        circuit.noop(2)
    circuit.barrier(1, 2)
    circuit.rz(p, 5)

    expected_circuit = QuantumCircuit(6)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.cx(0, 1)
        expected_circuit.cx(3, 4)
        expected_circuit.x(2)
    expected_circuit.barrier(1, 2)
    expected_circuit.rz(p, 5)

    yield circuit, expected_circuit, "consecutive_boxes_merged"


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
    """Test `GroupGatesIntoBoxes`.

    Args:
        circuits_to_compare: A tuple containing a ``(circuit, expected_circuit)`` pair.
    """
    circuit, expected_circuit = circuits_to_compare
    pm = PassManager(passes=[MergeBoxes()])
    transpiled_circuit = pm.run(circuit)

    assert transpiled_circuit == expected_circuit
