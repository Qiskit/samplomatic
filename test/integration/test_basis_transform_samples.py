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

"""Tests that twirling samples are produced correctly from static circuits."""

import numpy as np
from qiskit.circuit import BoxOp, QuantumCircuit
from qiskit.quantum_info import Operator, average_gate_fidelity

from samplomatic.annotations import BasisTransform, Twirl
from samplomatic.builders import pre_build


def make_circuits():
    circuit = QuantumCircuit(1)
    with circuit.box([BasisTransform()]):
        circuit.measure_all()

    expected = QuantumCircuit(1)
    expected.h(0)

    pauli = np.array([1], dtype=np.uint8)
    yield (circuit, expected, {"measure": pauli}), "x_basis_measure"

    expected = QuantumCircuit(1)
    expected.ry(-np.pi / 2, 0)

    pauli = np.array([3], dtype=np.uint8)
    yield (circuit, expected, {"measure": pauli}), "y_basis_measure"

    expected = QuantumCircuit(1)

    pauli = np.array([2], dtype=np.uint8)
    yield (circuit, expected, {"measure": pauli}), "z_basis_measure"

    circuit = QuantumCircuit(1)
    with circuit.box([BasisTransform(mode="prepare")]):
        circuit.noop(0)

    expected = QuantumCircuit(1)
    expected.h(0)

    pauli = np.array([1], dtype=np.uint8)
    yield (circuit, expected, {"prepare": pauli}), "x_basis_prepare"

    expected = QuantumCircuit(1)
    expected.ry(np.pi / 2, 0)

    pauli = np.array([3], dtype=np.uint8)
    yield (circuit, expected, {"prepare": pauli}), "y_basis_prepare"

    expected = QuantumCircuit(1)

    pauli = np.array([2], dtype=np.uint8)
    yield (circuit, expected, {"prepare": pauli}), "z_basis_prepare"

    circuit = QuantumCircuit(1)
    with circuit.box([BasisTransform()]):
        circuit.rx(np.pi / 4, 0)
        circuit.measure_all()

    expected = QuantumCircuit(1)
    expected.rx(np.pi / 4, 0)
    expected.h(0)

    pauli = np.array([1], dtype=np.uint8)
    yield (circuit, expected, {"measure": pauli}), "x_basis_sq_gate_measure"

    circuit = QuantumCircuit(1)
    with circuit.box([BasisTransform(mode="prepare")]):
        circuit.rx(np.pi / 4, 0)

    expected = QuantumCircuit(1)
    expected.h(0)
    expected.rx(np.pi / 4, 0)

    pauli = np.array([1], dtype=np.uint8)
    yield (circuit, expected, {"prepare": pauli}), "x_basis_sq_gate_prepare"

    circuit = QuantumCircuit(1)
    with circuit.box([BasisTransform(), Twirl()]):
        circuit.rx(np.pi / 4, 0)

    with circuit.box([Twirl(dressing="right")]):
        circuit.noop(0)

    expected = QuantumCircuit(1)
    expected.rx(np.pi / 4, 0)
    expected.h(0)

    pauli = np.array([1], dtype=np.uint8)
    yield (circuit, expected, {"measure": pauli}), "x_basis_twirl_measure"

    circuit = QuantumCircuit(1)
    with circuit.box([Twirl()]):
        circuit.noop(0)

    with circuit.box([BasisTransform(mode="prepare"), Twirl(dressing="right")]):
        circuit.rx(np.pi / 4, 0)

    expected = QuantumCircuit(1)
    expected.h(0)
    expected.rx(np.pi / 4, 0)

    pauli = np.array([1], dtype=np.uint8)
    yield (circuit, expected, {"prepare": pauli}), "x_basis_twirl_prepare"

    circuit = QuantumCircuit(2)
    with circuit.box([BasisTransform()]):
        circuit.noop(0, 1)

    expected = QuantumCircuit(2)
    expected.h(0)
    expected.h(1)

    pauli = np.array([1, 1], dtype=np.uint8)
    yield (circuit, expected, {"measure": pauli}), "xx_basis"

    circuit = QuantumCircuit(2)
    with circuit.box([BasisTransform(ref="my_basis0")]):
        circuit.noop(0, 1)
    with circuit.box([BasisTransform(ref="my_basis1")]):
        circuit.noop(0, 1)

    expected = QuantumCircuit(2)
    expected.h(0)
    expected.h(1)
    expected.ry(-np.pi / 2, 0)
    expected.ry(-np.pi / 2, 1)

    pauli_0 = np.array([1, 1], dtype=np.uint8)
    pauli_1 = np.array([3, 3], dtype=np.uint8)
    yield (
        (circuit, expected, {"my_basis0": pauli_0, "my_basis1": pauli_1}),
        "basis_change_multi_box",
    )

    circuit = QuantumCircuit(1)
    with circuit.box([BasisTransform(mode="prepare", ref="my_basis")]):
        circuit.noop(0)

    circuit.z(0)

    with circuit.box([BasisTransform(ref="my_basis")]):
        circuit.noop(0)

    expected = QuantumCircuit(1)
    expected.x(0)

    pauli = np.array([1], dtype=np.uint8)
    yield (circuit, expected, {"my_basis": pauli}), "z_to_x"

    pauli = np.array([1, 0, 0], dtype=np.uint8)
    expected = QuantumCircuit(3)
    expected.h(0)
    for idx, perm in enumerate([(0, 1, 2), (1, 2, 0), (2, 0, 1)]):
        circuit = QuantumCircuit(3)
        with circuit.box([BasisTransform(mode="prepare")]):
            circuit.noop(*perm)
        yield (circuit, expected, {"prepare": pauli}), f"permuted_context_qubits_{idx}"

    pauli = np.array([1, 0, 0], dtype=np.uint8)
    for idx, perm in enumerate([(0, 1, 2), (2, 0, 1), (1, 2, 0)]):
        circuit = QuantumCircuit(3)
        box_op = BoxOp(QuantumCircuit(3), annotations=[BasisTransform(mode="prepare")])
        circuit.append(box_op, perm)
        expected = QuantumCircuit(3)
        expected.h(idx)
        yield (circuit, expected, {"prepare": pauli}), f"permuted_box_op_qubits_{idx}"


def pytest_generate_tests(metafunc):
    if "circuit" in metafunc.fixturenames:
        args, descriptions = zip(*make_circuits())
        metafunc.parametrize("circuit,expected,basis_transforms", list(args), ids=descriptions)


def test_sampling(circuit, expected, basis_transforms, save_plot):
    """Test sampling.

    Casts the given ``circuit`` and the twirled circuit into operators, and it compares their
    fidelities.
    """
    save_plot(lambda: circuit.draw("mpl"), "Base Circuit", delayed=True)

    template, samplex_state = pre_build(circuit)
    save_plot(lambda: template.template.draw("mpl"), "Template Circuit", delayed=True)
    save_plot(lambda: samplex_state.draw(), "Unfinalized Pre-Samplex", delayed=True)

    samplex = samplex_state.finalize()
    samplex.finalize()
    save_plot(lambda: samplex_state.draw(), "Finalized Pre-Samplex", delayed=True)
    save_plot(lambda: samplex.draw(), "Samplex", delayed=True)

    samplex_input = samplex.inputs().bind(basis_changes=basis_transforms)
    samplex_output = samplex.sample(samplex_input, num_randomizations=10)
    parameter_values = samplex_output["parameter_values"]

    expected_op = Operator(expected)
    template.template.remove_final_measurements()
    for row in parameter_values:
        op = Operator(template.template.assign_parameters(row))
        assert np.allclose(f := average_gate_fidelity(expected_op, op), 1), f
