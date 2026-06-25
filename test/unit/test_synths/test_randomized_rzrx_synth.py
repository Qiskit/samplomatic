# This code is a Qiskit project.
#
# (C) Copyright IBM 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import numpy as np
import pytest
from qiskit.circuit import Parameter, ParameterVector, QuantumCircuit, QuantumRegister
from qiskit.quantum_info import Operator, average_gate_fidelity

from samplomatic.distributions import HaarU2
from samplomatic.exceptions import SynthError
from samplomatic.synths import RandomizedRzRxSynth
from samplomatic.virtual_registers import PauliRegister, VirtualType


def test_make_template():
    """Test that we can make a template."""
    synth = RandomizedRzRxSynth()
    qubits = QuantumRegister(5)
    params = [Parameter("a"), Parameter("b"), Parameter("c"), Parameter("d"), Parameter("e")]

    instructions = list(synth.make_template(qubits[5:6], iter(params)))
    assert len(instructions) == 5

    assert instructions[0].operation.name == "rz"
    assert list(instructions[0].qubits) == list(qubits[5:6])
    assert list(instructions[0].params) == [params[0]]

    assert instructions[1].operation.name == "rx"
    assert list(instructions[1].qubits) == list(qubits[5:6])
    assert list(instructions[1].params) == [params[1]]

    assert instructions[2].operation.name == "rz"
    assert list(instructions[2].qubits) == list(qubits[5:6])
    assert list(instructions[2].params) == [params[2]]

    assert instructions[3].operation.name == "rx"
    assert list(instructions[3].qubits) == list(qubits[5:6])
    assert list(instructions[3].params) == [params[3]]

    assert instructions[4].operation.name == "rz"
    assert list(instructions[4].qubits) == list(qubits[5:6])
    assert list(instructions[4].params) == [params[4]]


def test_make_template_fails():
    """Test that making a template fails when expected."""
    synth = RandomizedRzRxSynth()
    with pytest.raises(SynthError, match="Not enough parameters"):
        list(synth.make_template(QuantumRegister(1), iter([Parameter("a")])))


def test_requires_rng(rng):
    """Test that generate_template_values raises without an rng."""
    synth = RandomizedRzRxSynth()
    reg = PauliRegister(np.zeros((1, 5), dtype=np.uint8))
    with pytest.raises(SynthError, match="requires an rng"):
        synth.generate_template_values(reg)


def test_incompatible_register(rng):
    """Test that incompatible register types raise."""
    from samplomatic.virtual_registers import Z2Register

    synth = RandomizedRzRxSynth()
    reg = Z2Register(np.zeros((1, 5), dtype=np.uint8))
    with pytest.raises(SynthError, match="not understood"):
        synth.generate_template_values(reg, rng)


def test_generate_params_correctness_u2(rng):
    """Test that generated template parameters are correct for U2Registers."""
    u2 = HaarU2(2).sample(11, rng)
    synth = RandomizedRzRxSynth()

    circuit = QuantumCircuit(2)
    parameters = iter(ParameterVector("p", 10))
    for qubit in circuit.qubits:
        for instr in synth.make_template([qubit], parameters):
            circuit.append(instr)

    template_parameters = synth.generate_template_values(u2, rng)
    assert template_parameters.shape == (2, 11, 5)

    for idx, sample in enumerate(template_parameters.transpose(1, 0, 2)):
        circuit_unitary = Operator(circuit.assign_parameters(sample.ravel()))
        reg_unitary = Operator(u2.virtual_gates[1, idx]) ^ Operator(u2.virtual_gates[0, idx])
        assert np.isclose(average_gate_fidelity(circuit_unitary, reg_unitary), 1)


def test_generate_params_correctness_pauli(rng):
    """Test that generated template parameters are correct for PauliRegisters."""
    gates = np.tile(np.arange(4, dtype=np.uint8), (2, 25))
    reg = PauliRegister(gates)
    synth = RandomizedRzRxSynth()

    circuit = QuantumCircuit(1)
    parameters = iter(ParameterVector("p", 5))
    for instr in synth.make_template([circuit.qubits[0]], parameters):
        circuit.append(instr)

    template_parameters = synth.generate_template_values(reg, rng)
    assert template_parameters.shape == (2, 100, 5)

    pauli_matrices = np.array(
        [
            np.diag([1, 1]),
            np.diag([1, -1]),
            np.diag([1, 1])[::-1],
            np.diag([-1j, 1j])[::-1],
        ],
        dtype=complex,
    )

    for sub in range(2):
        for idx in range(100):
            angles = template_parameters[sub, idx]
            circuit_unitary = Operator(circuit.assign_parameters(angles))
            pauli_idx = gates[sub, idx]
            target = Operator(pauli_matrices[pauli_idx])
            assert np.isclose(
                average_gate_fidelity(circuit_unitary, target), 1
            ), f"Failed for Pauli idx={pauli_idx}, subsystem={sub}, sample={idx}"


def test_pauli_rx_angles_vary(rng):
    """Test that rx angles are randomized across samples."""
    gates = np.zeros((1, 500), dtype=np.uint8)
    reg = PauliRegister(gates)
    synth = RandomizedRzRxSynth()

    values = synth.generate_template_values(reg, rng)
    rx_angles = values[0, :, 3]

    assert rx_angles.std() > 0.5
    assert rx_angles.min() < 0.5
    assert rx_angles.max() > 2.5


def test_pauli_x_rx_angles_complementary(rng):
    """Test that X Pauli samples have δ₁ + δ₂ = π."""
    gates = np.full((1, 200), 2, dtype=np.uint8)
    reg = PauliRegister(gates)
    synth = RandomizedRzRxSynth()

    values = synth.generate_template_values(reg, rng)
    delta1 = values[0, :, 3]
    delta2 = values[0, :, 1]
    np.testing.assert_allclose(delta1 + delta2, np.pi, atol=1e-14)


def test_pauli_i_rx_angles_symmetric(rng):
    """Test that I Pauli samples have δ₁ = δ₂."""
    gates = np.zeros((1, 200), dtype=np.uint8)
    reg = PauliRegister(gates)
    synth = RandomizedRzRxSynth()

    values = synth.generate_template_values(reg, rng)
    delta1 = values[0, :, 3]
    delta2 = values[0, :, 1]
    np.testing.assert_allclose(delta1, delta2, atol=1e-14)


def test_u2_rx_angles_vary(rng):
    """Test that rx angles are randomized for U2 registers."""
    u2 = HaarU2(1).sample(500, rng)
    synth = RandomizedRzRxSynth()

    values = synth.generate_template_values(u2, rng)
    rx_angles = values[0, :, 3]

    assert rx_angles.std() > 0.3
    assert rx_angles.min() < 1.0
    assert rx_angles.max() > 2.0


def test_deterministic_with_same_seed():
    """Test that results are deterministic given the same seed."""
    gates = np.tile(np.arange(4, dtype=np.uint8), (1, 50))
    reg = PauliRegister(gates)
    synth = RandomizedRzRxSynth()

    values1 = synth.generate_template_values(reg, np.random.default_rng(123))
    values2 = synth.generate_template_values(reg, np.random.default_rng(123))
    np.testing.assert_array_equal(values1, values2)


def test_different_seeds_differ():
    """Test that different seeds produce different results."""
    gates = np.zeros((1, 50), dtype=np.uint8)
    reg = PauliRegister(gates)
    synth = RandomizedRzRxSynth()

    values1 = synth.generate_template_values(reg, np.random.default_rng(1))
    values2 = synth.generate_template_values(reg, np.random.default_rng(2))
    assert not np.allclose(values1, values2)


def test_u2_cliffords_correctness(rng):
    """Test that Clifford U2 gates are correctly synthesized."""
    from samplomatic.virtual_registers import C1Register

    all_c1 = C1Register(np.arange(24, dtype=C1Register.DTYPE).reshape(1, -1))
    all_u2 = all_c1.convert_to(VirtualType.U2)
    synth = RandomizedRzRxSynth()

    circuit = QuantumCircuit(1)
    parameters = iter(ParameterVector("p", 5))
    for instr in synth.make_template([circuit.qubits[0]], parameters):
        circuit.append(instr)

    template_parameters = synth.generate_template_values(all_u2, rng)

    for idx, angles in enumerate(template_parameters.reshape(-1, 5)):
        u2 = all_u2.virtual_gates[0, idx]
        circuit_unitary = Operator(circuit.assign_parameters(angles))
        assert np.isclose(
            average_gate_fidelity(circuit_unitary, Operator(u2)), 1
        ), f"Failed for C1={idx}"
