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
from qiskit.circuit import ClassicalRegister, Parameter, QuantumCircuit, QuantumRegister

from samplomatic import build
from samplomatic.transpiler import generate_boxing_pass_manager


def make_circuits():
    circuit = QuantumCircuit(1)

    yield circuit, "empty_circuit"

    circuit = QuantumCircuit(3)
    circuit.cx(0, 1)
    circuit.x(0)
    circuit.x(1)
    circuit.barrier(1)
    circuit.z(1)
    circuit.x(2)
    circuit.cx(0, 1)
    circuit.x(1)
    circuit.barrier(0, 1)
    circuit.cx(0, 1)
    circuit.cx(0, 2)
    circuit.barrier(0, 1, 2)
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

    yield circuit, "circuit_with_boxes_and_barriers"

    circuit = QuantumCircuit(QuantumRegister(6, "q"), ClassicalRegister(6, "c"))
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
@pytest.mark.parametrize("measure_annotations", ["twirl", "basis_transform", "all"])
@pytest.mark.parametrize("twirling_strategy", ["active", "active-accum", "active-circuit", "all"])
@pytest.mark.parametrize("remove_barriers", [True, False])
def test_generate_boxing_pass_manager_makes_buildable_circuits(
    circuit, enable_gates, enable_measure, measure_annotations, twirling_strategy, remove_barriers
):
    """Test `generate_boxing_pass_manager`.

    Args:
        circuit: The circuit to try and build
    """
    pm = generate_boxing_pass_manager(
        enable_gates=enable_gates,
        enable_measure=enable_measure,
        measure_annotations=measure_annotations,
        twirling_strategy=twirling_strategy,
        remove_barriers=remove_barriers,
    )
    transpiled_circuit = pm.run(circuit)

    build(transpiled_circuit)
