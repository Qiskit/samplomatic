# This code is a Qiskit project.
#
# (C) Copyright IBM 2025, 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Test the GroupGatesIntoBoxes"""

import numpy as np
import pytest
from qiskit.circuit import Parameter, QuantumCircuit, QuantumRegister
from qiskit.transpiler import PassManager
from qiskit.transpiler.exceptions import TranspilerError

from samplomatic.annotations import Twirl
from samplomatic.transpiler.passes import GroupGatesIntoBoxes


def make_circuits():
    theta = Parameter("theta")
    phi = Parameter("phi")
    lam = Parameter("lambda")

    circuit = QuantumCircuit(1)

    expected_circuit = QuantumCircuit(1)

    yield circuit, expected_circuit, "empty_circuit"

    circuit = QuantumCircuit(3)
    circuit.rx(np.pi / 3, 0)
    circuit.rz(np.pi / 8, 0)
    circuit.h(0)
    circuit.y(2)

    expected_circuit = QuantumCircuit(3)
    expected_circuit.rx(np.pi / 3, 0)
    expected_circuit.rz(np.pi / 8, 0)
    expected_circuit.h(0)
    expected_circuit.y(2)

    yield circuit, expected_circuit, "circuit_with_only_single-qubit_gates"

    qregs = [QuantumRegister(4, "alpha"), QuantumRegister(2, "beta")]
    circuit = QuantumCircuit(*qregs)
    circuit.cx(1, 2)
    circuit.cx(4, 3)
    circuit.x(0)
    circuit.rx(theta, 0)
    circuit.z(1)

    expected_circuit = QuantumCircuit(*qregs)
    expected_circuit.x(0)
    expected_circuit.rx(theta, 0)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.cx(1, 2)
        expected_circuit.cx(4, 3)
    expected_circuit.z(1)

    yield circuit, expected_circuit, "multiple_quantum_registers"

    circuit = QuantumCircuit(6)
    circuit.cx(0, 1)
    circuit.cx(1, 2)
    circuit.cx(2, 3)
    circuit.cx(3, 4)
    circuit.cx(4, 5)
    circuit.cx(4, 3)

    expected_circuit = QuantumCircuit(6)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.cx(0, 1)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.cx(1, 2)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.cx(2, 3)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.cx(3, 4)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.cx(4, 5)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.cx(4, 3)

    yield circuit, expected_circuit, "each_gate_in_a_separate_box"

    circuit = QuantumCircuit(6)
    circuit.x(0)
    circuit.rx(theta, 0)
    circuit.rz(phi, 1)
    circuit.z(0)
    circuit.y(1)
    circuit.cx(1, 2)
    circuit.cx(4, 3)
    circuit.ecr(0, 1)
    circuit.y(1)
    circuit.sx(3)
    circuit.rz(lam, 5)
    circuit.sx(5)

    expected_circuit = QuantumCircuit(6)
    expected_circuit.rz(phi, 1)
    expected_circuit.y(1)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.cx(4, 3)
        expected_circuit.cx(1, 2)
    expected_circuit.x(0)
    expected_circuit.rx(theta, 0)
    expected_circuit.z(0)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.ecr(0, 1)
    expected_circuit.sx(3)
    expected_circuit.y(1)
    expected_circuit.rz(lam, 5)
    expected_circuit.sx(5)

    yield circuit, expected_circuit, "each_box_contains_single_and_multi-qubit_gates"

    circuit = QuantumCircuit(4)
    circuit.cx(0, 1)
    circuit.x(0)
    circuit.z(1)
    circuit.y(2)
    circuit.h(3)
    circuit.barrier(1, 2)
    circuit.cx(2, 3)

    expected_circuit = QuantumCircuit(4)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.cx(0, 1)
    expected_circuit.z(1)
    expected_circuit.y(2)
    expected_circuit.barrier(1, 2)
    expected_circuit.h(3)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.cx(2, 3)
    expected_circuit.x(0)

    yield circuit, expected_circuit, "circuit_with_partial_width_barrier"

    circuit = QuantumCircuit(3)
    circuit.cx(0, 1)
    circuit.x(0)
    circuit.y(0)
    circuit.t(1)
    circuit.barrier()
    circuit.z(1)
    circuit.h(2)
    circuit.y(2)

    expected_circuit = QuantumCircuit(3)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.cx(0, 1)
    expected_circuit.x(0)
    expected_circuit.y(0)
    expected_circuit.t(1)
    expected_circuit.barrier()
    expected_circuit.z(1)
    expected_circuit.h(2)
    expected_circuit.y(2)

    yield circuit, expected_circuit, "circuit_with_full_width_barrier"

    circuit = QuantumCircuit(4)
    circuit.cx(0, 1)
    circuit.barrier()
    circuit.cx(2, 3)

    expected_circuit = QuantumCircuit(4)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.cx(0, 1)
    expected_circuit.barrier()
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.cx(2, 3)

    yield circuit, expected_circuit, "circuit_with_barrier_after_a_non_collected_two_qubit_gate"

    circuit = QuantumCircuit(3)
    circuit.cx(0, 1)
    circuit.x(0)
    circuit.x(1)
    with circuit.box():
        circuit.noop(1)
    circuit.z(1)
    circuit.x(2)
    circuit.cx(0, 1)
    circuit.x(1)
    with circuit.box():
        circuit.noop(0, 1)
    circuit.cx(0, 1)
    circuit.cx(0, 2)
    with circuit.box():
        circuit.noop(0, 1, 2)
    circuit.x(0)
    circuit.x(1)

    expected_circuit = QuantumCircuit(3)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.cx(0, 1)
    expected_circuit.x(1)
    with expected_circuit.box():
        expected_circuit.noop(1)
    expected_circuit.x(0)
    expected_circuit.z(1)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.cx(0, 1)
    expected_circuit.x(1)
    with expected_circuit.box():
        expected_circuit.noop(0, 1)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.cx(0, 1)
    expected_circuit.x(2)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.cx(0, 2)
    with expected_circuit.box():
        expected_circuit.noop(0, 1, 2)
    expected_circuit.x(0)
    expected_circuit.x(1)

    yield circuit, expected_circuit, "circuit_with_partial_width_and_full_width_boxes"

    circuit = QuantumCircuit(4, 2)
    circuit.cx(0, 1)
    circuit.x(0)
    circuit.t(1)
    circuit.measure(1, 0)
    circuit.measure(2, 0)
    circuit.cx(2, 3)
    circuit.barrier()
    circuit.cx(0, 1)
    circuit.measure(1, 0)
    circuit.measure(2, 1)
    circuit.cx(2, 3)

    expected_circuit = QuantumCircuit(4, 2)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.cx(0, 1)
    expected_circuit.x(0)
    expected_circuit.t(1)
    expected_circuit.measure(1, 0)
    expected_circuit.measure(2, 0)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.cx(2, 3)
    expected_circuit.barrier()
    expected_circuit.measure(2, 1)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.cx(0, 1)
        expected_circuit.cx(2, 3)
    expected_circuit.measure(1, 0)

    yield circuit, expected_circuit, "circuit_with_measurements"

    circuit = QuantumCircuit(7)
    for _ in range(2):
        circuit.cz(2, 3)
        circuit.cz(4, 5)
        circuit.cz(1, 6)
        circuit.cz(0, 1)
        circuit.cz(3, 4)
        circuit.cz(5, 6)
        circuit.sx([3, 5])
        circuit.sx([3, 5])

    expected_circuit = QuantumCircuit(7)
    with expected_circuit.box([Twirl()]):
        expected_circuit.cz(2, 3)
        expected_circuit.cz(4, 5)
        expected_circuit.cz(1, 6)
    with expected_circuit.box([Twirl()]):
        expected_circuit.cz(0, 1)
        expected_circuit.cz(3, 4)
        expected_circuit.cz(5, 6)
    expected_circuit.sx([3, 5])
    expected_circuit.sx([3, 5])
    with expected_circuit.box([Twirl()]):
        expected_circuit.cz(2, 3)
        expected_circuit.cz(4, 5)
        expected_circuit.cz(1, 6)
    with expected_circuit.box([Twirl()]):
        expected_circuit.cz(0, 1)
        expected_circuit.cz(3, 4)
        expected_circuit.cz(5, 6)
    expected_circuit.sx([3, 5])
    expected_circuit.sx([3, 5])

    yield circuit, expected_circuit, "circuit_with_long_range_czs"

    circuit = QuantumCircuit(4, 3)
    circuit.cx(0, 1)
    circuit.measure([1, 2], [0, 0])  # two meas on the same bit
    circuit.cx(2, 3)
    circuit.barrier()
    circuit.cx(0, 1)
    circuit.measure([1, 2], [1, 2])  # two meas on two different bits
    circuit.cx(2, 3)

    expected_circuit = QuantumCircuit(4, 3)
    with expected_circuit.box([Twirl()]):
        expected_circuit.cx(0, 1)
    expected_circuit.measure([1, 2], [0, 0])
    with expected_circuit.box([Twirl()]):
        expected_circuit.cx(2, 3)
    expected_circuit.barrier()
    expected_circuit.measure(2, 2)
    with expected_circuit.box([Twirl()]):
        expected_circuit.cx(0, 1)
        expected_circuit.cx(2, 3)
    expected_circuit.measure(1, 1)

    yield circuit, expected_circuit, "circuit_with_measurements_on_same_bit"


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
    if "alap_circuits_to_compare" in metafunc.fixturenames:
        alap_circuits = [*make_alap_circuits()]
        real_and_expected = [(test[0], test[1]) for test in alap_circuits]
        descriptions = [test[2] for test in alap_circuits]
        metafunc.parametrize("alap_circuits_to_compare", real_and_expected, ids=descriptions)


def test_transpiled_circuits_have_correct_boxops(circuits_to_compare):
    """Test `GroupGatesIntoBoxes`.

    Args:
        circuits_to_compare: A tuple containing a ``(circuit, expected_circuit)`` pair.
    """
    circuit, expected_circuit = circuits_to_compare
    pm = PassManager(passes=[GroupGatesIntoBoxes()])
    transpiled_circuit = pm.run(circuit)

    assert transpiled_circuit == expected_circuit


@pytest.mark.parametrize("annotations", [(), (Twirl(dressing="right"),), (Twirl(),)])
def test_annotations(annotations):
    """Test that we can set the annotation."""
    circuit = QuantumCircuit(4)
    circuit.cx(0, 1)
    circuit.barrier()
    circuit.cx(2, 3)

    expected_circuit = QuantumCircuit(4)
    with expected_circuit.box(list(annotations)):
        expected_circuit.cx(0, 1)
    expected_circuit.barrier()
    with expected_circuit.box(list(annotations)):
        expected_circuit.cx(2, 3)

    pm = PassManager(passes=[GroupGatesIntoBoxes(annotations)])
    transpiled_circuit = pm.run(circuit)

    assert transpiled_circuit == expected_circuit


def make_alap_circuits():
    """Yield (circuit, expected_alap_circuit, description) triples for ALAP-specific tests."""
    theta = Parameter("theta")
    phi = Parameter("phi")
    lam = Parameter("lambda")

    # In ASAP: cx(1,2)+cx(4,3) share no qubits → same box; ecr(0,1) follows in a second box.
    # In ALAP: ecr(0,1) is latest → group 0; cx(1,2) shares q1 with ecr → pushed to group -1;
    #          cx(4,3) shares no qubits with ecr → also lands in group 0 alongside ecr.
    circuit = QuantumCircuit(6)
    circuit.x(0)
    circuit.rx(theta, 0)
    circuit.rz(phi, 1)
    circuit.z(0)
    circuit.y(1)
    circuit.cx(1, 2)
    circuit.cx(4, 3)
    circuit.ecr(0, 1)
    circuit.y(1)
    circuit.sx(3)
    circuit.rz(lam, 5)
    circuit.sx(5)

    expected_circuit = QuantumCircuit(6)
    expected_circuit.rz(phi, 1)
    expected_circuit.y(1)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.cx(1, 2)
    expected_circuit.x(0)
    expected_circuit.rx(theta, 0)
    expected_circuit.z(0)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.ecr(0, 1)
        expected_circuit.cx(4, 3)
    expected_circuit.y(1)
    expected_circuit.sx(3)
    expected_circuit.rz(lam, 5)
    expected_circuit.sx(5)

    yield circuit, expected_circuit, "alap_groups_independent_gate_with_latest_box"

    # Partial-width barrier: barrier(1,2) splits groups only on qubits 1 and 2.
    # In ALAP: cx(2,3) is latest → group 0; barrier(1,2) pushes q1,q2 to group -1;
    # cx(0,1) touches q1 which is now at -1 → group -1.
    circuit = QuantumCircuit(4)
    circuit.cx(0, 1)
    circuit.x(0)
    circuit.z(1)
    circuit.y(2)
    circuit.h(3)
    circuit.barrier(1, 2)
    circuit.cx(2, 3)

    expected_circuit = QuantumCircuit(4)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.cx(0, 1)
    expected_circuit.x(0)
    expected_circuit.z(1)
    expected_circuit.y(2)
    expected_circuit.barrier(1, 2)
    expected_circuit.h(3)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.cx(2, 3)

    yield circuit, expected_circuit, "alap_circuit_with_partial_width_barrier"

    # Full-width barrier: all qubits flushed. CX gates on either side cannot merge.
    circuit = QuantumCircuit(4)
    circuit.cx(0, 1)
    circuit.barrier()
    circuit.cx(2, 3)

    expected_circuit = QuantumCircuit(4)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.cx(0, 1)
    expected_circuit.barrier()
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.cx(2, 3)

    yield circuit, expected_circuit, "alap_circuit_with_full_width_barrier"

    # Measurements as delimiters in ALAP mode.
    # In ALAP traversal (reverse): cx(2,3) after barrier → group 0, cx(0,1) after barrier →
    # group 0 (shares no constrained bits). Barrier pushes all to -1. Before barrier: cx(2,3)
    # → group -1; measure syncs q1/c0 at -1 (no further push); cx(0,1) touches q1 at -1 →
    # also group -1. So both pre-barrier CX gates share a box.
    circuit = QuantumCircuit(4, 1)
    circuit.cx(0, 1)
    circuit.measure(1, 0)
    circuit.cx(2, 3)
    circuit.barrier()
    circuit.cx(0, 1)
    circuit.cx(2, 3)

    expected_circuit = QuantumCircuit(4, 1)
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.cx(0, 1)
        expected_circuit.cx(2, 3)
    expected_circuit.measure(1, 0)
    expected_circuit.barrier()
    with expected_circuit.box([Twirl(dressing="left")]):
        expected_circuit.cx(0, 1)
        expected_circuit.cx(2, 3)

    yield circuit, expected_circuit, "alap_circuit_with_measurements"


def test_raises_for_unsupported_ops():
    """Test that `GroupGatesIntoBoxes` raises when the circuit contains unsupported ops."""
    pm = PassManager(passes=[GroupGatesIntoBoxes()])

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


def test_alap_transpiled_circuits_have_correct_boxops(alap_circuits_to_compare):
    """Test ``GroupGatesIntoBoxes`` with ``alap=True``.

    Args:
        alap_circuits_to_compare: A tuple containing a ``(circuit, expected_circuit)`` pair where
            the expected circuit reflects ALAP box grouping.
    """
    circuit, expected_circuit = alap_circuits_to_compare
    pm = PassManager(passes=[GroupGatesIntoBoxes(strategy="alap")])
    transpiled_circuit = pm.run(circuit)

    assert transpiled_circuit == expected_circuit


def test_alap_and_asap_agree_on_fully_constrained_circuits():
    """Test that ALAP and ASAP produce the same result when gate order is uniquely determined."""
    circuit = QuantumCircuit(6)
    circuit.cx(0, 1)
    circuit.cx(1, 2)
    circuit.cx(2, 3)
    circuit.cx(3, 4)
    circuit.cx(4, 5)

    pm_asap = PassManager(passes=[GroupGatesIntoBoxes()])
    pm_alap = PassManager(passes=[GroupGatesIntoBoxes(strategy="alap")])

    assert pm_asap.run(circuit) == pm_alap.run(circuit)
