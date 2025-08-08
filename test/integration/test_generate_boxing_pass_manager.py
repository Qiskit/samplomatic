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

"""Test that `generate_boxing_pass_manager` generates buildable circuits."""

import pytest
from qiskit.circuit import Parameter, QuantumCircuit, QuantumRegister

from samplomatic import build
from samplomatic.transpiler import generate_boxing_pass_manager


def make_circuits():
    theta = Parameter("theta")
    phi = Parameter("phi")
    lam = Parameter("lambda")

    circuit = QuantumCircuit(1)

    yield circuit, "empty_circuit"

    qregs = [QuantumRegister(4, "alpha"), QuantumRegister(2, "beta")]
    circuit = QuantumCircuit(*qregs)
    circuit.cx(1, 2)
    circuit.cx(4, 3)
    circuit.x(0)
    circuit.rx(theta, 0)
    circuit.z(1)

    yield circuit, "multiple_quantum_registers"

    circuit = QuantumCircuit(6)
    circuit.cx(0, 1)
    circuit.cx(1, 2)
    circuit.cx(2, 3)
    circuit.cx(3, 4)
    circuit.cx(4, 5)
    circuit.cx(4, 3)

    yield circuit, "each_gate_in_a_separate_box"

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

    yield circuit, "each_box_contains_single_and_multi-qubit_gates"

    circuit = QuantumCircuit(4)
    circuit.cx(0, 1)
    circuit.x(0)
    circuit.z(1)
    circuit.y(2)
    circuit.h(3)
    circuit.barrier(1, 2)
    circuit.cx(2, 3)

    yield circuit, "circuit_with_partial_width_barrier"

    circuit = QuantumCircuit(3)
    circuit.cx(0, 1)
    circuit.x(0)
    circuit.y(0)
    circuit.t(1)
    circuit.barrier()
    circuit.z(1)
    circuit.h(2)
    circuit.y(2)

    yield circuit, "circuit_with_full_width_barrier"

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

    yield circuit, "circuit_with_partial_width_and_full_width_boxes"

    circuit = QuantumCircuit(4, 4)
    circuit.measure(1, 0)
    circuit.measure(2, 1)
    circuit.cx(1, 2)
    circuit.measure(1, 2)
    circuit.measure(2, 3)

    yield circuit, "circuit_with_measurements"

    circuit = QuantumCircuit(3, 2)
    circuit.sdg(0)
    circuit.barrier(0, 1)
    circuit.x(0)
    circuit.z(0)
    circuit.y(1)
    circuit.ecr(0, 1)
    circuit.t(1)
    circuit.measure(0, 0)
    circuit.measure(1, 1)
    circuit.x(0)
    circuit.y(0)
    circuit.z(1)
    circuit.measure_all()

    yield circuit, "circuit_with_barriers_and_measurements"

    circuit = QuantumCircuit(6, 6)
    for layer_idx in range(8):
        for qubit_idx in range(circuit.num_qubits):
            circuit.rz(Parameter(f"theta_{layer_idx}_{qubit_idx}"), qubit_idx)
            circuit.sx(qubit_idx)
            circuit.rz(Parameter(f"phi_{layer_idx}_{qubit_idx}"), qubit_idx)
            circuit.sx(qubit_idx)
            circuit.rz(Parameter(f"lam_{layer_idx}_{qubit_idx}"), qubit_idx)
        circuit.cx(0, 1)
        circuit.cx(2, 3)
        circuit.cx(4, 5)
    circuit.measure_all()

    yield circuit, "utility_type_circuit"


def pytest_generate_tests(metafunc):
    if "circuit" in metafunc.fixturenames:
        circuit_and_description = [*make_circuits()]
        circuit = [test[0] for test in circuit_and_description]
        description = [test[1] for test in circuit_and_description]
        metafunc.parametrize("circuit", circuit, ids=description)


@pytest.mark.parametrize("enable_gates", [True, False])
@pytest.mark.parametrize("enable_measure", [True, False])
@pytest.mark.parametrize("twirling_strategy", ["active", "active-accum", "active-circuit", "all"])
@pytest.mark.parametrize(
    "inject_noise_strategy",
    ["none", "no_modification", "uniform_modification", "individual_modification"],
)
def test_generate_boxing_pass_manager_makes_buildable_circuits(
    circuit, enable_gates, enable_measure, twirling_strategy, inject_noise_strategy
):
    """Test `generate_boxing_pass_manager`.

    Args:
        circuit: The circuit to try and build
    """
    pm = generate_boxing_pass_manager(
        enable_gates,
        enable_measure,
        twirling_strategy,
        inject_noise_strategy,
    )
    transpiled_circuit = pm.run(circuit)

    build(transpiled_circuit)
