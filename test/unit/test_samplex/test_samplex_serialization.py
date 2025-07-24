# This code is part of the Samplomatic project.
#
# This is proprietary IBM software for internal use only, do not distribute outside of IBM
# Unauthorized copying of this file is strictly prohibited
#
# (C) Copyright IBM 2025.

from qiskit.circuit import Parameter, QuantumCircuit

from samplomatic.annotations import Twirl
from samplomatic import build
from samplomatic.samplex.samplex_serialization import samplex_to_json, samplex_from_json


class TestSamplexSerialization:
    """Test serialization of samplex objects."""

    def test_general_5q_static_circuit(self):
        """Test with a general static circuit of 5 qubits"""

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

        _template_state, samplex = build(circuit)
        json_data = samplex_to_json(samplex)
        print(json_data)
        samplex_new = samplex_from_json(json_data)
        print(samplex_new)
        assert samplex == samplex_new
