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


from qiskit.circuit import QuantumCircuit

from samplomatic import build
from samplomatic.annotations import Twirl
from samplomatic.samplex.samplex_serialization import samplex_from_json, samplex_to_json


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
