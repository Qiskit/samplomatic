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
from qiskit.quantum_info import Operator, average_gate_fidelity

from samplomatic.distributions import HaarU2
from samplomatic.exceptions import SynthError
from samplomatic.synths import RzRxSynth


def test_make_template():
    """Test that we can make a template."""
    synth = RzRxSynth()
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
    synth = RzRxSynth()
    with pytest.raises(SynthError, match="Not enough parameters"):
        list(synth.make_template(QuantumRegister(1), iter([Parameter("a")])))


def test_generate_params_correctness_u2(rng):
    """Test that generated template parameters are correct for U2Registers."""
    u2 = HaarU2(2).sample(11, rng)
    synth = RzRxSynth()

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
