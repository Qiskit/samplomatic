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
from copy import deepcopy

import numpy as np
from qiskit.circuit import Parameter, ParameterVector, QuantumCircuit
from qiskit.quantum_info import QubitSparsePauliList

from samplomatic import build
from samplomatic.annotations import BasisTransform, InjectNoise, Twirl
from samplomatic.samplex.samplex_serialization import samplex_from_json, samplex_to_json


class TestSamplexSerialization:
    """Test serialization of samplex objects."""

    def test_general_5q_static_circuit(self, rng):
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
        json_data = samplex_to_json(samplex)
        assert isinstance(json_data, str)

        samplex_new = samplex_from_json(json_data)

        samplex.finalize()
        samplex_new.finalize()

        copy_rng = deepcopy(rng)
        samplex_output = samplex.sample(samplex.inputs(), rng=rng)
        samplex_new_output = samplex_new.sample(samplex.inputs(), rng=copy_rng)
        np.testing.assert_allclose(
            samplex_output["parameter_values"], samplex_new_output["parameter_values"]
        )

    def test_noise_injection_circuit(self, rng):
        """Test a circuit with inject noise annotations."""
        circuit = QuantumCircuit(2)
        with circuit.box([Twirl(), InjectNoise("my_noise", "my_modifier")]):
            circuit.noop(range(2))

        with circuit.box([Twirl(dressing="right")]):
            circuit.noop(range(2))

        _, samplex = build(circuit)
        samplex_new = samplex_from_json(samplex_to_json(samplex))

        samplex.finalize()
        samplex_new.finalize()

        paulis = QubitSparsePauliList.from_list(["XX"])
        samplex_input = samplex.inputs({"my_noise": paulis}).bind(
            noise_maps={"rates.my_noise": [0.5]}
        )
        samplex_new_input = samplex_new.inputs({"my_noise": paulis}).bind(
            noise_maps={"rates.my_noise": [0.5]}
        )
        copy_rng = deepcopy(rng)

        samplex_output = samplex.sample(samplex_input, rng=rng)
        samplex_new_output = samplex_new.sample(samplex_new_input, rng=copy_rng)
        np.testing.assert_allclose(
            samplex_output["parameter_values"], samplex_new_output["parameter_values"]
        )
        np.testing.assert_allclose(samplex_output["pauli_signs"], samplex_new_output["pauli_signs"])

    def test_basis_transform_circuit(self, rng):
        """Test a circuit with basis transform annotations."""
        circuit = QuantumCircuit(2)
        with circuit.box([BasisTransform()]):
            circuit.noop(range(2))

        with circuit.box([Twirl()]):
            circuit.measure_all()

        basis = np.array([2, 1], dtype=np.uint8)

        _, samplex = build(circuit)
        samplex_new = samplex_from_json(samplex_to_json(samplex))

        samplex.finalize()
        samplex_new.finalize()

        samplex_input = samplex.inputs().bind(basis_changes={"measure": basis})
        copy_rng = deepcopy(rng)

        samplex_output = samplex.sample(samplex_input, rng=rng)
        samplex_new_output = samplex_new.sample(samplex_input, rng=copy_rng)
        np.testing.assert_allclose(
            samplex_output["parameter_values"], samplex_new_output["parameter_values"]
        )
        np.testing.assert_allclose(
            samplex_output["measurement_flips.meas"], samplex_new_output["measurement_flips.meas"]
        )

    def test_parametric_circuit(self, rng):
        """Test a circuit with parametric gates."""
        p = ParameterVector("params", 5)
        circuit = QuantumCircuit(3)
        with circuit.box([Twirl()]):
            circuit.rx(p[0], 0)
            circuit.rx(p[1], 1)
            circuit.rx(p[2], 2)
            circuit.cx(0, 1)

        with circuit.box([Twirl()]):
            circuit.rx(p[3], 0)
            circuit.rx(p[4], 1)
            circuit.cx(0, 1)

        with circuit.box([Twirl(dressing="right")]):
            circuit.noop(range(3))

        circuit_params = rng.random(len(circuit.parameters))

        _, samplex = build(circuit)
        samplex_new = samplex_from_json(samplex_to_json(samplex))

        samplex.finalize()
        samplex_new.finalize()

        samplex_input = samplex.inputs().bind(parameter_values=circuit_params)
        copy_rng = deepcopy(rng)

        samplex_output = samplex.sample(samplex_input, rng=rng)
        samplex_new_output = samplex_new.sample(samplex_input, rng=copy_rng)
        np.testing.assert_allclose(
            samplex_output["parameter_values"], samplex_new_output["parameter_values"]
        )

    def test_passthrough_params_circuit(self, rng):
        """Test a circuit with passthrough paramemeters."""
        circuit = QuantumCircuit(2)
        circuit.rx(Parameter("a"), 0)
        circuit.rx(Parameter("b"), 1)
        circuit.rx(Parameter("c"), 0)

        circuit_params = rng.random(len(circuit.parameters))

        _, samplex = build(circuit)
        samplex_new = samplex_from_json(samplex_to_json(samplex))

        samplex.finalize()
        samplex_new.finalize()

        samplex_input = samplex.inputs().bind(parameter_values=circuit_params)
        copy_rng = deepcopy(rng)

        samplex_output = samplex.sample(samplex_input, rng=rng)
        samplex_new_output = samplex_new.sample(samplex_input, rng=copy_rng)

        np.testing.assert_allclose(
            samplex_output["parameter_values"], samplex_new_output["parameter_values"]
        )
