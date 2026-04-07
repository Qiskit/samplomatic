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

import numpy as np
import pytest
from qiskit.circuit import Parameter, ParameterVector, QuantumCircuit, QuantumRegister
from qiskit.quantum_info import Clifford, Operator, average_gate_fidelity

from samplomatic.distributions import HaarU2
from samplomatic.exceptions import SynthError
from samplomatic.synths import RzSxSynth
from samplomatic.virtual_registers import C1Register, VirtualType


def test_make_template():
    """Test that we can make a template."""
    synth = RzSxSynth()
    qubits = QuantumRegister(5)
    params = [Parameter("a"), Parameter("b"), Parameter("c")]

    instructions = list(synth.make_template(qubits[5:6], iter(params)))
    assert len(instructions) == 5

    assert instructions[0].operation.name == "rz"
    assert list(instructions[0].qubits) == list(qubits[5:6])
    assert list(instructions[0].params) == [params[0]]

    assert instructions[1].operation.name == "sx"
    assert list(instructions[1].qubits) == list(qubits[5:6])

    assert instructions[2].operation.name == "rz"
    assert list(instructions[2].qubits) == list(qubits[5:6])
    assert list(instructions[2].params) == [params[1]]

    assert instructions[3].operation.name == "sx"
    assert list(instructions[3].qubits) == list(qubits[5:6])

    assert instructions[4].operation.name == "rz"
    assert list(instructions[4].qubits) == list(qubits[5:6])
    assert list(instructions[4].params) == [params[2]]


def test_make_template_fails():
    """Test that making a template fails when expected."""
    synth = RzSxSynth()
    with pytest.raises(SynthError, match="Not enough parameters"):
        list(synth.make_template(QuantumRegister(1), iter([Parameter("a")])))


def test_generate_params_correctness_u2(rng):
    """Test that generated template parameters are correct for U2Registers."""
    u2 = HaarU2(2).sample(11, rng)
    synth = RzSxSynth()

    circuit = QuantumCircuit(2)
    parameters = iter(ParameterVector("p", 6))
    for qubit in circuit.qubits:
        for instr in synth.make_template([qubit], parameters):
            circuit.append(instr)

    template_parameters = synth.generate_template_values(u2)
    assert template_parameters.shape == (2, 11, 3)

    for idx, sample in enumerate(template_parameters.transpose(1, 0, 2)):
        circuit_unitary = Operator(circuit.assign_parameters(sample.ravel()))
        reg_unitary = Operator(u2.virtual_gates[1, idx]) ^ Operator(u2.virtual_gates[0, idx])
        assert np.isclose(average_gate_fidelity(circuit_unitary, reg_unitary), 1)


def test_u2_cliffords_make_cliffords(rng):
    """Test that clifford gates synthesize to clifford angles."""
    all_c1 = C1Register(np.arange(0, 60, dtype=C1Register.DTYPE).reshape(1, -1) % 24)
    all_u2 = all_c1.convert_to(VirtualType.U2)
    synth = RzSxSynth()

    # mess around with numerical precision and global phases
    all_u2.virtual_gates[0, 25:26] *= np.exp(1j * 1e-15)
    all_u2.virtual_gates[0, 26:27] *= np.exp(1j * -1e-15)
    all_u2.virtual_gates[0, 25:26] += 1e-16
    all_u2.virtual_gates[0, 26:27] -= 1e-16
    all_u2.virtual_gates[0, 25:] *= np.exp(1j * rng.random((35, 1, 1)))

    circuit = QuantumCircuit(1)
    parameters = iter(ParameterVector("p", 3))
    for qubit in circuit.qubits:
        for instr in synth.make_template([qubit], parameters):
            circuit.append(instr)

    template_parameters = synth.generate_template_values(all_u2)
    tableaus = all_c1.to_tableau()

    for idx, angles in enumerate(template_parameters.reshape(-1, 3)):
        c1 = all_c1.virtual_gates[0, idx]
        u2 = all_u2.virtual_gates[0, idx]

        # check all angles yield Clifford rotations
        is_clifford = np.array([False] * 3)
        for angle in [-np.pi / 2, 0, np.pi / 2, np.pi]:
            is_clifford |= np.isclose(angles, angle)
        assert np.all(is_clifford), f"Angles for C1={c1} are not Clifford: {angles}"

        # check we have the Clifford we should
        circuit_cliff = Clifford(circuit.assign_parameters(angles))
        assert circuit_cliff == Clifford(tableaus[0, idx]), f"Found tableau inequality for C1={c1}"

        # check for unitary synthesis correctness
        circuit_unitary = Operator(circuit.assign_parameters(angles))
        assert np.isclose(average_gate_fidelity(circuit_unitary, Operator(u2)), 1)
