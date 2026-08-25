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

"""Test gate-dependent twirl buidling."""

import numpy as np
import pytest
from qiskit.circuit import Parameter, QuantumCircuit

from samplomatic import Twirl
from samplomatic.annotations import GroupMode
from samplomatic.builders import pre_build
from samplomatic.exceptions import BuildError
from samplomatic.pre_samplex import PreEmit


class TestGateDependetTwirling:
    def test_multiple_2q_gates_local_c1(self):
        """Test left-dressed local_c1 box has multiple two-qubit gate emissions."""
        circuit = QuantumCircuit(4)
        with circuit.box([Twirl(group="local_c1", dressing="left")]):
            circuit.cx(0, 1)
            circuit.cz(2, 3)

        with circuit.box([Twirl(dressing="right")]):
            circuit.noop(0, 1, 2, 3)

        _, pre_samplex = pre_build(circuit)
        pre_emits = [node for node in pre_samplex.graph.nodes() if isinstance(node, PreEmit)]

        assert len(pre_emits) == 3
        assert any(n.twirl_gate == "cz" and n.register_type == "local_c1" for n in pre_emits)
        assert any(n.twirl_gate == "cx" and n.register_type == "local_c1" for n in pre_emits)
        assert any(n.twirl_gate is None and n.register_type == "pauli" for n in pre_emits)

    def test_multiple_2q_gate_local_pauli(self):
        """Test left-dressed local_pauli box has multiple two-qubit gate emissions."""
        circuit = QuantumCircuit(4)
        with circuit.box([Twirl(group="local_pauli", dressing="left")]):
            circuit.rzz(Parameter("a"), 0, 1)
            circuit.cz(2, 3)
            circuit.measure_all()

        _, pre_samplex = pre_build(circuit)
        pre_emits = [node for node in pre_samplex.graph.nodes() if isinstance(node, PreEmit)]

        assert len(pre_emits) == 2
        assert any(n.twirl_gate == "rzz" and n.register_type == "local_pauli" for n in pre_emits)
        assert any(n.twirl_gate is None and n.register_type == "pauli" for n in pre_emits)

    def test_overlapping_rzzs_local_pauli(self):
        """Error when a local_pauli box has overlapping RZZs."""
        circuit = QuantumCircuit(3)
        with circuit.box([Twirl(group="local_pauli", dressing="left")]):
            circuit.rzz(Parameter("a"), 0, 1)
            circuit.rzz(Parameter("b"), 1, 2)
            circuit.measure_all()

        with pytest.raises(BuildError, match="with multiple two-qubit gates from"):
            pre_build(circuit)

    def test_overlapping_gates_local_pauli(self):
        """Error when a local_pauli box has overlapping RZZ with another entangler."""
        circuit = QuantumCircuit(3)
        with circuit.box([Twirl(group="local_pauli", dressing="left")]):
            circuit.rzz(Parameter("a"), 0, 1)
            circuit.cz(1, 2)
            circuit.measure_all()

        with pytest.raises(BuildError, match="other entanglers"):
            pre_build(circuit)

        circuit = QuantumCircuit(3)
        with circuit.box([Twirl(group="local_pauli", dressing="left")]):
            circuit.cz(1, 2)
            circuit.rzz(Parameter("a"), 0, 1)
            circuit.measure_all()

        with pytest.raises(BuildError, match="other entanglers"):
            pre_build(circuit)

    def test_2q_gate_local_pauli_clifford_angle(self):
        """Test local_pauli falls back to pauli for fractional gates at Clifford angles."""
        circuit = QuantumCircuit(4)
        with circuit.box([Twirl(group="local_pauli", dressing="left")]):
            circuit.rzz(np.pi / 2, 0, 1)
            circuit.measure_all()

        _, pre_samplex = pre_build(circuit)
        pre_emits = [node for node in pre_samplex.graph.nodes() if isinstance(node, PreEmit)]

        assert len(pre_emits) == 1
        assert any(n.twirl_gate is None and n.register_type == "pauli" for n in pre_emits)

    def test_overlapping_2q_gates_same_pair(self):
        """Error when a local_c1 box has duplicate two-qubit gates on the same qubits."""
        circuit = QuantumCircuit(2)
        with circuit.box([Twirl(group="local_c1", dressing="left")]):
            circuit.cx(0, 1)
            circuit.h(0)
            circuit.cx(0, 1)

        with circuit.box([Twirl(dressing="right")]):
            circuit.noop(0, 1)

        with pytest.raises(BuildError, match=f"Cannot use `{GroupMode.LOCAL_C1}`"):
            pre_build(circuit)

    def test_overlapping_2q_gates_different_pairs(self):
        """Error when a local_c1 box has two-qubit gates on partially overlapping qubits."""
        circuit = QuantumCircuit(3)
        with circuit.box([Twirl(group="local_c1", dressing="left")]):
            circuit.cx(0, 1)
            circuit.cx(1, 2)

        with circuit.box([Twirl(dressing="right")]):
            circuit.noop(0, 1, 2)

        with pytest.raises(BuildError, match=f"Cannot use `{GroupMode.LOCAL_C1}`"):
            pre_build(circuit)

    def test_measurement_with_c1_twirl(self):
        """Error when local_c1 resolves to C1 in a box with measurements."""
        circuit = QuantumCircuit(2, 2)
        with circuit.box([Twirl(group="local_c1", dressing="left")]):
            circuit.cx(0, 1)
            circuit.measure(0, 0)

        with pytest.raises(BuildError, match="twirl in a box with measurements"):
            pre_build(circuit)

        circuit = QuantumCircuit(3, 1)
        with circuit.box([Twirl(group="local_c1", dressing="left")]):
            circuit.cx(0, 1)
            circuit.measure(2, 0)

        with circuit.box([Twirl(group="pauli", dressing="right")]):
            circuit.cx(0, 1)

        with pytest.raises(BuildError, match="twirl in a box with measurements"):
            pre_build(circuit)
