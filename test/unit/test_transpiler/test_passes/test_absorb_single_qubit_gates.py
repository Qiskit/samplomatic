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

"""Test the AbsorbSingleQubitGates"""

from qiskit.circuit import Parameter, QuantumCircuit
from qiskit.transpiler import PassManager

from samplomatic import ChangeBasis, Twirl
from samplomatic.transpiler.passes import AbsorbSingleQubitGates


def make_circuits():
    """Yield (circuit, expected_circuit, description) for comprehensive absorption scenarios."""
    theta = Parameter("theta")
    phi = Parameter("phi")
    lam = Parameter("lambda")

    circuit = QuantumCircuit(1)
    expected_circuit = QuantumCircuit(1)
    yield circuit, expected_circuit, "empty_circuit"

    circuit = QuantumCircuit(3)
    circuit.x(0)
    circuit.ry(theta, 1)
    circuit.z(2)

    expected_circuit = QuantumCircuit(3)
    expected_circuit.x(0)
    expected_circuit.ry(theta, 1)
    expected_circuit.z(2)
    yield circuit, expected_circuit, "only_1q_gates_no_boxes"

    circuit = QuantumCircuit(1)
    circuit.x(0)
    circuit.y(0)
    with circuit.box():
        circuit.rz(phi, 0)

    expected_circuit = QuantumCircuit(1)
    with expected_circuit.box():
        expected_circuit.x(0)
        expected_circuit.y(0)
        expected_circuit.rz(phi, 0)
    yield circuit, expected_circuit, "absorb_run_into_1q_box"

    circuit = QuantumCircuit(2)
    circuit.rx(theta, 0)
    circuit.z(1)
    with circuit.box():
        circuit.cx(0, 1)

    expected_circuit = QuantumCircuit(2)
    with expected_circuit.box():
        expected_circuit.rx(theta, 0)
        expected_circuit.z(1)
        expected_circuit.cx(0, 1)
    yield circuit, expected_circuit, "absorb_run_into_2q_box_both_wires"

    circuit = QuantumCircuit(5)
    circuit.id(3)
    circuit.x(1)
    circuit.y(2)
    circuit.z(0)
    with circuit.box():
        circuit.cx(2, 0)
        circuit.cz(3, 1)

    expected_circuit = QuantumCircuit(5)
    with expected_circuit.box():
        expected_circuit.id(3)
        expected_circuit.x(1)
        expected_circuit.y(2)
        expected_circuit.z(0)
        expected_circuit.cx(2, 0)
        expected_circuit.cz(3, 1)
    yield circuit, expected_circuit, "absorb_run_into_2q_box_all_wires_permuted"

    circuit = QuantumCircuit(5)
    circuit.id(3)
    circuit.x(1)
    circuit.y(2)
    circuit.z(0)
    with circuit.box():
        circuit.cx(2, 0)
        circuit.noop(range(5))

    expected_circuit = QuantumCircuit(5)
    with expected_circuit.box():
        expected_circuit.id(3)
        expected_circuit.x(1)
        expected_circuit.y(2)
        expected_circuit.z(0)
        expected_circuit.cx(2, 0)
        expected_circuit.noop(4)
    yield circuit, expected_circuit, "noops_present"

    circuit = QuantumCircuit(1, 1)
    circuit.x(0)
    circuit.measure(0, 0)  # interruption
    circuit.z(0)
    with circuit.box():
        circuit.rz(lam, 0)

    expected_circuit = QuantumCircuit(1, 1)
    expected_circuit.x(0)
    expected_circuit.measure(0, 0)
    with expected_circuit.box():
        expected_circuit.z(0)
        expected_circuit.rz(lam, 0)
    yield circuit, expected_circuit, "interrupted_by_measure_only_post_measure_absorbs"

    circuit = QuantumCircuit(1)
    circuit.y(0)
    circuit.barrier(0)  # interruption
    circuit.x(0)
    with circuit.box():
        circuit.h(0)

    expected_circuit = QuantumCircuit(1)
    expected_circuit.y(0)
    expected_circuit.barrier(0)
    with expected_circuit.box():
        expected_circuit.x(0)
        expected_circuit.h(0)
    yield circuit, expected_circuit, "barrier_interrupts_run"

    circuit = QuantumCircuit(2)
    circuit.x(0)
    circuit.cx(0, 1)  # interruption
    circuit.y(0)
    with circuit.box():
        circuit.rz(phi, 0)

    expected_circuit = QuantumCircuit(2)
    expected_circuit.x(0)
    expected_circuit.cx(0, 1)
    with expected_circuit.box():
        expected_circuit.y(0)
        expected_circuit.rz(phi, 0)
    yield circuit, expected_circuit, "entangler_interrupts_run"

    circuit = QuantumCircuit(2)
    circuit.x(0)
    circuit.barrier()  # global interruption
    circuit.ry(theta, 1)
    with circuit.box():
        circuit.cx(0, 1)

    expected_circuit = QuantumCircuit(2)
    expected_circuit.x(0)
    expected_circuit.barrier()
    with expected_circuit.box():
        expected_circuit.ry(theta, 1)
        expected_circuit.cx(0, 1)
    yield circuit, expected_circuit, "global_barrier_breaks_runs_disjoint_wires"

    circuit = QuantumCircuit(1)
    circuit.x(0)
    with circuit.box():
        circuit.h(0)
    with circuit.box():
        circuit.rz(phi, 0)

    expected_circuit = QuantumCircuit(1)
    with expected_circuit.box():
        expected_circuit.x(0)
        expected_circuit.h(0)
    with expected_circuit.box():
        expected_circuit.rz(phi, 0)
    yield circuit, expected_circuit, "multiple_boxes_back_to_back_absorb_first_only"

    circuit = QuantumCircuit(2)
    circuit.y(0)
    circuit.rx(theta, 1)
    circuit.rz(lam, 0)
    with circuit.box():
        circuit.cz(0, 1)

    expected_circuit = QuantumCircuit(2)
    with expected_circuit.box():
        expected_circuit.y(0)
        expected_circuit.rx(theta, 1)
        expected_circuit.rz(lam, 0)
        expected_circuit.cz(0, 1)
    yield circuit, expected_circuit, "runs_on_both_wires_absorb"

    circuit = QuantumCircuit(1)
    circuit.x(0)
    circuit.y(0)
    circuit.z(0)
    with circuit.box():
        circuit.h(0)

    expected_circuit = QuantumCircuit(1)
    with expected_circuit.box():
        expected_circuit.x(0)
        expected_circuit.y(0)
        expected_circuit.z(0)
        expected_circuit.h(0)
    yield circuit, expected_circuit, "absorption_order_correctness"

    circuit = QuantumCircuit(1)
    circuit.x(0)

    expected_circuit = QuantumCircuit(1)
    expected_circuit.x(0)
    yield circuit, expected_circuit, "end_of_circuit_no_successor"


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
    """Test GroupGatesIntoBoxes."""
    circuit, expected_circuit = circuits_to_compare
    pm = PassManager(passes=[AbsorbSingleQubitGates()])
    transpiled_circuit = pm.run(circuit)

    assert transpiled_circuit == expected_circuit


def test_annotation_preservation():
    """Test that annotations are preserved."""
    circuit = QuantumCircuit(3)
    circuit.x(0)
    with circuit.box(annotations=[Twirl()]):
        circuit.cx(0, 1)
    circuit.x(1)
    with circuit.box(annotations=[Twirl(dressing="right"), ChangeBasis()]):
        circuit.cx(2, 1)

    pm = PassManager(passes=[AbsorbSingleQubitGates()])
    transpiled_circuit = pm.run(circuit)

    assert transpiled_circuit[0].operation.annotations == [Twirl()]
    assert transpiled_circuit[0].operation.annotations is not circuit[1].operation.annotations
    assert transpiled_circuit[1].operation.annotations == [Twirl(dressing="right"), ChangeBasis()]
