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


import pytest
from qiskit.circuit import Parameter, ParameterVector, QuantumCircuit

from samplomatic import build
from samplomatic.annotations import ChangeBasis, InjectNoise, Twirl
from samplomatic.exceptions import SerializationError
from samplomatic.serialization import samplex_from_json, samplex_to_json
from samplomatic.ssv import SSV

SUPPORTED_SSVS = {SSV}


class TestSamplexSerialization:
    """Test serialization of samplex functions."""

    def test_samplex_to_json_errors(self):
        """Test errors are raised when serializing a samplex with a bad SSV."""
        circuit = QuantumCircuit(1)
        with circuit.box([ChangeBasis()]):
            circuit.noop(0)
        _, samplex = build(circuit)

        with pytest.raises(SerializationError):
            samplex_to_json(samplex, ssv=0)

        with pytest.raises(SerializationError):
            samplex_to_json(samplex, ssv=9999)

    @pytest.mark.parametrize("ssv", SUPPORTED_SSVS)
    def test_general_5q_static_circuit(self, ssv):
        """Test with a general static circuit of 5 qubits."""
        circuit = QuantumCircuit(5)
        with circuit.box([Twirl()]):
            circuit.rz(0.5, 0)
            circuit.sx(0)
            circuit.rz(0.5, 0)
            circuit.cx(0, 3)
            circuit.noop(range(5))

        circuit.cx(0, 1)

        with circuit.box([Twirl(decomposition="rzrx")]):
            circuit.rz(0.123, 2)
            circuit.cx(3, 4)
            circuit.cx(3, 2)
            circuit.noop(1)

        with circuit.box([Twirl()]):
            circuit.cx(0, 1)

        with circuit.box([Twirl(dressing="right")]):
            circuit.noop(range(5))

        circuit.measure_all()

        _, samplex = build(circuit)
        json_data = samplex_to_json(samplex, ssv=ssv)
        assert isinstance(json_data, str)

        samplex_new = samplex_from_json(json_data)
        samplex_new.finalize()

        assert samplex == samplex_new

    @pytest.mark.parametrize("ssv", SUPPORTED_SSVS)
    def test_noise_injection_circuit(self, ssv):
        """Test a circuit with inject noise annotations."""
        circuit = QuantumCircuit(2)
        with circuit.box([Twirl(), InjectNoise("my_noise", "my_modifier")]):
            circuit.noop(range(2))

        with circuit.box([Twirl(dressing="right")]):
            circuit.noop(range(2))

        _, samplex = build(circuit)
        samplex_new = samplex_from_json(samplex_to_json(samplex, ssv=ssv))
        samplex_new.finalize()

        assert samplex == samplex_new

    @pytest.mark.parametrize("ssv", SUPPORTED_SSVS)
    def test_change_basis_circuit(self, ssv):
        """Test a circuit with basis change annotations."""
        circuit = QuantumCircuit(2)
        with circuit.box([ChangeBasis()]):
            circuit.noop(range(2))

        with circuit.box([Twirl()]):
            circuit.measure_all()

        _, samplex = build(circuit)
        samplex_new = samplex_from_json(samplex_to_json(samplex, ssv=ssv))
        samplex_new.finalize()

        assert samplex == samplex_new

    @pytest.mark.parametrize("ssv", SUPPORTED_SSVS)
    @pytest.mark.parametrize(
        "parameters",
        [
            ParameterVector("params", 5),
            [Parameter(f"p{idx}") for idx in range(5)],
            list(ParameterVector("params", 3)) + [Parameter(f"p{idx}") for idx in range(2)],
            [Parameter(f"p{idx}") for idx in range(3)] + list(ParameterVector("params", 2)),
        ],
    )
    def test_parametric_circuit(self, parameters, ssv):
        """Test a circuit with parametric gates."""
        circuit = QuantumCircuit(3)
        with circuit.box([Twirl()]):
            circuit.rx(parameters[0], 0)
            circuit.rx(parameters[1], 1)
            circuit.rx(parameters[2], 2)
            circuit.cx(0, 1)

        with circuit.box([Twirl()]):
            circuit.rx(parameters[3] + parameters[0], 0)
            circuit.rx(2 * parameters[4], 1)
            circuit.cx(0, 1)

        with circuit.box([Twirl(dressing="right")]):
            circuit.noop(range(3))

        _, samplex = build(circuit)
        samplex_new = samplex_from_json(samplex_to_json(samplex, ssv=ssv))
        samplex_new.finalize()

        assert samplex == samplex_new

    @pytest.mark.parametrize("ssv", SUPPORTED_SSVS)
    def test_passthrough_params_circuit(self, ssv):
        """Test a circuit with passthrough paramemeters."""
        circuit = QuantumCircuit(2)
        circuit.rx(Parameter("a"), 0)
        circuit.rx(Parameter("b"), 1)
        circuit.rx(Parameter("c"), 0)

        _, samplex = build(circuit)
        samplex_new = samplex_from_json(samplex_to_json(samplex, ssv=ssv))
        samplex_new.finalize()

        assert samplex == samplex_new
