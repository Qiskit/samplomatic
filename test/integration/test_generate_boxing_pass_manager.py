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
from qiskit.circuit.library import CZGate, RXGate, RZGate, RZZGate, SXGate, XGate
from qiskit.transpiler import PassManager, Target, generate_preset_pass_manager
from qiskit.transpiler.passes import RemoveBarriers

from samplomatic import build
from samplomatic.transpiler import generate_boxing_pass_manager
from samplomatic.transpiler.passes import InlineBoxes
from samplomatic.utils import find_unique_box_instructions


@pytest.fixture
def linear_target():
    """Construct a simple six-qubit target on a line."""
    num_qubits = 6
    target = Target(num_qubits=num_qubits)

    # Add single-qubit gates (sx, rz, rx)
    for gate_obj in [SXGate(), RZGate(Parameter("p")), RXGate(Parameter("p")), XGate()]:
        target.add_instruction(gate_obj, properties={(q,): None for q in range(num_qubits)})

    # Add two-qubit gates (cz, rzz) with coupling map
    coupling_map = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (0, 5)]
    for gate_obj in [CZGate(), RZZGate(Parameter("p"))]:
        properties = {pair: None for pair in coupling_map}
        target.add_instruction(gate_obj, properties)

    yield target


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
@pytest.mark.parametrize("enable_measures", [True, False])
@pytest.mark.parametrize("measure_annotations", ["twirl", "change_basis", "all"])
@pytest.mark.parametrize("twirling_strategy", ["active", "active_accum", "active_circuit", "all"])
@pytest.mark.parametrize(
    "remove_barriers", ["immediately", "finally", "after_stratification", "never"]
)
def test_generate_boxing_pass_manager_makes_buildable_circuits(
    circuit, enable_gates, enable_measures, measure_annotations, twirling_strategy, remove_barriers
):
    """Test ``generate_boxing_pass_manager`` produces buildable, logically equivalent circuits."""
    pm = generate_boxing_pass_manager(
        enable_gates=enable_gates,
        enable_measures=enable_measures,
        measure_annotations=measure_annotations,
        twirling_strategy=twirling_strategy,
        remove_barriers=remove_barriers,
    )
    transpiled_circuit = pm.run(circuit)

    # ensure buildable
    build(transpiled_circuit)

    # ensure if we get rid of all barriers and boxes, nothing has been changed
    flattening_pm = PassManager([RemoveBarriers(), InlineBoxes()])
    unboxed_transpiled_circuit = flattening_pm.run(transpiled_circuit)
    unboxed_circuit = flattening_pm.run(circuit)
    assert unboxed_circuit == unboxed_transpiled_circuit


def test_qiskit_pm_integration_with_trotterized_circuit(linear_target):
    """Test that integrating boxing pass with qiskit PM interacts with trotter circuit nicely."""
    # Do the boxing passes after we perform all scheduling-like passes.
    pm = generate_preset_pass_manager(
        target=linear_target,
        layout_method="trivial",
        optimization_level=2,
    )
    pm.post_scheduling = generate_boxing_pass_manager(
        enable_gates=True,
        enable_measures=True,
        twirling_strategy="active_circuit",
        inject_noise_targets="gates",
        remove_barriers="after_stratification",
    )

    # make a simple trotterized circuit on 6 qubits that obey the linear target
    circuit = QuantumCircuit(6)
    layers = [[(0, 1), (2, 3), (4, 5)], [(1, 2), (3, 4)], [(0, 5)]]
    parameters = [Parameter(f"p{idx}") for idx in range(6)]
    for _ in range(num_steps := 1):
        for layer in layers:
            for idx, param in enumerate(parameters):
                circuit.rx(param, idx)
            circuit.barrier()
            for pair in layer:
                circuit.cx(*pair)
            circuit.barrier()

    transpiled_circuit = pm.run(circuit)

    # every step should result in 3 boxes, and then one at the end for the final single-qubit gates
    assert len(transpiled_circuit) == num_steps * len(layers) + 1

    # because of all of the barriers, there should be one unique box per original layer, plus empty
    assert len(find_unique_box_instructions(transpiled_circuit)) == len(layers) + 1

    # ensure it's buildable
    build(transpiled_circuit)
