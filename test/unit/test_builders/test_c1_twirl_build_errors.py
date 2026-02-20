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

"""Test error cases for local_c1 twirling."""

import pytest
from qiskit.circuit import QuantumCircuit

from samplomatic import Twirl
from samplomatic.builders import pre_build
from samplomatic.exceptions import BuildError


class TestLocalC1BuildErrors:
    def test_multiple_2q_gate_types_left(self):
        """Error when a left-dressed local_c1 box has multiple 2Q gate types."""
        circuit = QuantumCircuit(4)
        with circuit.box([Twirl(group="local_c1", dressing="left")]):
            circuit.cx(0, 1)
            circuit.cz(2, 3)

        with circuit.box([Twirl(dressing="right")]):
            circuit.noop(0, 1, 2, 3)

        with pytest.raises(BuildError, match="multiple 2Q gate types"):
            pre_build(circuit)

    def test_multiple_2q_gate_types_right(self):
        """Error when a right-dressed local_c1 box has multiple 2Q gate types."""
        circuit = QuantumCircuit(4)
        with circuit.box([Twirl(group="local_c1", dressing="left")]):
            circuit.noop(0, 1, 2, 3)

        with circuit.box([Twirl(group="local_c1", dressing="right")]):
            circuit.cx(0, 1)
            circuit.cz(2, 3)

        with pytest.raises(BuildError, match="multiple 2Q gate types"):
            pre_build(circuit)

    def test_overlapping_2q_gates_same_pair(self):
        """Error when a local_c1 box has duplicate 2Q gates on the same qubits."""
        circuit = QuantumCircuit(2)
        with circuit.box([Twirl(group="local_c1", dressing="left")]):
            circuit.cx(0, 1)
            circuit.h(0)
            circuit.cx(0, 1)

        with circuit.box([Twirl(dressing="right")]):
            circuit.noop(0, 1)

        with pytest.raises(BuildError, match="duplicate 2Q gates"):
            pre_build(circuit)

    def test_overlapping_2q_gates_different_pairs(self):
        """Error when a local_c1 box has 2Q gates on partially overlapping qubits."""
        circuit = QuantumCircuit(3)
        with circuit.box([Twirl(group="local_c1", dressing="left")]):
            circuit.cx(0, 1)
            circuit.cx(1, 2)

        with circuit.box([Twirl(dressing="right")]):
            circuit.noop(0, 1, 2)

        with pytest.raises(BuildError, match="overlapping"):
            pre_build(circuit)

    def test_measurement_with_c1_twirl(self):
        """Error when local_c1 resolves to C1 in a box with measurements."""
        circuit = QuantumCircuit(2, 2)
        with circuit.box([Twirl(group="local_c1", dressing="left")]):
            circuit.cx(0, 1)
            circuit.measure(0, 0)

        with pytest.raises(BuildError, match="twirl in a box with measurements"):
            pre_build(circuit)
