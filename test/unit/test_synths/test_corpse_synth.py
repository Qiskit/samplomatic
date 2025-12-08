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

import numpy as np
import pytest
from qiskit.circuit import Parameter, ParameterVector, QuantumCircuit, QuantumRegister
from qiskit.circuit.library import RXGate, XGate
from qiskit.quantum_info import Operator, average_gate_fidelity
from scipy.linalg import expm

from samplomatic.distributions import HaarU2
from samplomatic.exceptions import SynthError
from samplomatic.synths import CorpseSynth, RzRxSynth


def u(theta, epsilon=0.0, delta=0.0) -> Operator:
    """Construct a 2x2 unitary for a single pulse with detuning and overrotation."""
    x = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
    z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
    theta_eff = (1.0 + epsilon) * theta
    return Operator(expm(-1.0j * ((delta / 2.0) * z + (theta_eff / 2.0) * x)))


def test_make_template():
    """Test that we can make a template."""
    synth = CorpseSynth()
    qubits = QuantumRegister(5)
    params = [Parameter("a"), Parameter("b"), Parameter("c")]

    instructions = list(synth.make_template(qubits[5:6], iter(params)))
    assert len(instructions) == 3

    assert instructions[0].operation.name == "rz"
    assert list(instructions[0].qubits) == list(qubits[5:6])
    assert list(instructions[0].params) == [params[0]]

    assert instructions[1].operation.name == "rx"
    assert list(instructions[1].qubits) == list(qubits[5:6])
    assert list(instructions[1].params) == [params[1]]

    assert instructions[2].operation.name == "rz"
    assert list(instructions[2].qubits) == list(qubits[5:6])
    assert list(instructions[2].params) == [params[2]]


def test_make_template_fails():
    """Test that making a template fails when expected."""
    synth = CorpseSynth()
    with pytest.raises(SynthError, match="Not enough parameters"):
        list(synth.make_template(QuantumRegister(1), iter([Parameter("a")])))


def test_generate_params_correctness_u2(rng):
    """Test that generated template parameters are correct for U2Registers."""
    u2 = HaarU2(2).sample(11, rng)
    synth = CorpseSynth()

    circuit = QuantumCircuit(2)
    parameters = iter(ParameterVector("p", 8))
    for qubit in circuit.qubits:
        for instr in synth.make_template([qubit], parameters):
            circuit.append(instr)

    template_parameters = synth.generate_template_values(u2)
    assert template_parameters.shape == (2, 11, 4)

    for idx, sample in enumerate(template_parameters.transpose(1, 0, 2)):
        circuit_unitary = Operator(circuit.assign_parameters(sample.ravel()))
        reg_unitary = Operator(u2.virtual_gates[1, idx]) ^ Operator(u2.virtual_gates[0, idx])
        assert np.isclose(average_gate_fidelity(circuit_unitary, reg_unitary), 1)


def test_robustness(rng):
    """Test that the sequence is more robust than naive sequence."""
    u2 = HaarU2(1).sample(num_samples := 11, rng)

    circuit_composite = QuantumCircuit(1)
    parameters = iter(ParameterVector("p", 5))
    for qubit in circuit_composite.qubits:
        for instr in CorpseSynth().make_template([qubit], parameters):
            circuit_composite.append(instr)

    circuit_simple = QuantumCircuit(1)
    parameters = iter(ParameterVector("p", 5))
    for qubit in circuit_simple.qubits:
        for instr in RzRxSynth().make_template([qubit], parameters):
            circuit_simple.append(instr)

    parameters_composite = CorpseSynth().generate_template_values(u2)
    parameters_simple = RzRxSynth().generate_template_values(u2)

    epsilon = 0
    delta = 0.3

    for idx in range(num_samples):
        unitary_composite = Operator(np.eye(2))
        for instr in circuit_composite.assign_parameters(parameters_composite[0, idx].ravel()):
            if isinstance(instr.operation, XGate):
                op = Operator(u(np.pi, epsilon=epsilon, delta=delta))
            elif isinstance(instr.operation, RXGate):
                op = Operator(u(instr.operation.params[0], epsilon=epsilon, delta=delta))
            else:
                op = Operator(instr.operation)
            unitary_composite = op @ unitary_composite

        unitary_simple = Operator(np.eye(2))
        for instr in circuit_simple.assign_parameters(parameters_simple[0, idx].ravel()):
            if isinstance(instr.operation, XGate):
                op = Operator(u(np.pi, epsilon=epsilon, delta=delta))
            elif isinstance(instr.operation, RXGate):
                op = Operator(u(instr.operation.params[0], epsilon=epsilon, delta=delta))
            else:
                op = Operator(instr.operation)
            unitary_simple = op @ unitary_simple

        unitary_ideal = Operator(u2.virtual_gates[0, idx])
        composite_fidelity = average_gate_fidelity(unitary_composite, unitary_ideal)
        simple_fidelity = average_gate_fidelity(unitary_simple, unitary_ideal)

        assert composite_fidelity > simple_fidelity
