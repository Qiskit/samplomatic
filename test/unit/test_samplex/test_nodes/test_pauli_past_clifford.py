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


from itertools import product

import numpy as np
import pytest
from qiskit.circuit.library import CXGate, CZGate, ECRGate, HGate
from qiskit.quantum_info import Clifford, Pauli

from samplomatic.annotations import VirtualType
from samplomatic.exceptions import SamplexBuildError
from samplomatic.samplex.nodes import PauliPastCliffordNode
from samplomatic.samplex.nodes.pauli_past_clifford_node import PAULI_PAST_CLIFFORD_LOOKUP_TABLES
from samplomatic.virtual_registers import PauliRegister


class TestLookupTables:
    paulis_1q = {
        0: Pauli("I"),
        1: Pauli("Z"),
        2: Pauli("X"),
        3: Pauli("Y"),
    }

    @pytest.mark.parametrize("op_class", [HGate])
    def test_1q_gate_tables(self, op_class):
        """Test the lookup tables for one-qubit gates."""
        op = op_class()
        clifford_op = Clifford.from_operator(op)
        table = PAULI_PAST_CLIFFORD_LOOKUP_TABLES[op.name]

        for pauli_idx in range(4):
            pauli_in = self.paulis_1q[pauli_idx]
            pauli_from_qiskit = pauli_in.evolve(clifford_op)
            pauli_from_table = self.paulis_1q[table[pauli_idx][0]]

            assert pauli_from_table.equiv(pauli_from_qiskit), (
                f"{pauli_in} through {op.name}: Table says {pauli_from_table}, "
                f"qiskit says {pauli_from_qiskit}."
            )

    @pytest.mark.parametrize("op_class", [CXGate, CZGate, ECRGate])
    def test_2q_gate_tables(self, op_class):
        """Test the lookup tables for two-qubit gates."""
        op = op_class()
        clifford_op = Clifford.from_operator(op)
        table = PAULI_PAST_CLIFFORD_LOOKUP_TABLES[op.name]

        for pauli0, pauli1 in product(range(4), repeat=2):
            pauli_in = self.paulis_1q[pauli1].tensor(self.paulis_1q[pauli0])
            pauli_from_qiskit = pauli_in.evolve(clifford_op)

            q0, q1 = table[pauli0, pauli1]
            pauli_from_table = self.paulis_1q[q1].tensor(self.paulis_1q[q0])

            assert pauli_from_table.equiv(pauli_from_qiskit), (
                f"{pauli_in} through {op.name}: Table says {pauli_from_table}, "
                f"qiskit says {pauli_from_qiskit}."
            )


class TestPauliPastClifford:
    def test_one_qubit_gate(self):
        """Test propagating Pauli register past a one-qubit Clifford gate."""
        node = PauliPastCliffordNode("h", "my_reg", [(3,), (1,), (0,)])

        reg = PauliRegister([[0, 1], [1, 2], [2, 0], [3, 1]])
        node.evaluate({"my_reg": reg}, np.empty(()))

        assert reg.virtual_gates.tolist() == [[0, 2], [2, 1], [2, 0], [3, 2]]
        assert node.outgoing_register_type is VirtualType.PAULI

    def test_cx_gate(self):
        """Test propagating Pauli register past a controlled-X gate."""
        node = PauliPastCliffordNode("cx", "my_reg", [(0, 1), (4, 2), (6, 5)])
        assert node.outgoing_register_type is VirtualType.PAULI

        reg = PauliRegister(
            [
                [1, 3, 2, 1, 2],
                [1, 2, 0, 3, 0],
                [3, 0, 1, 2, 0],
                [2, 1, 0, 1, 2],
                [0, 0, 1, 1, 0],
                [1, 2, 1, 2, 3],
                [1, 0, 3, 0, 1],
            ]
        )
        node.evaluate({"my_reg": reg}, np.empty(()))

        expected = [
            [0, 3, 2, 0, 2],
            [1, 0, 2, 3, 2],
            [3, 0, 1, 2, 0],
            [2, 1, 0, 1, 2],
            [1, 0, 0, 1, 0],
            [1, 2, 3, 2, 3],
            [0, 0, 2, 0, 0],
        ]
        assert reg.virtual_gates.tolist() == expected

    def test_init_error(self):
        """Test init error."""
        with pytest.raises(SamplexBuildError, match=", found hadamard."):
            PauliPastCliffordNode("hadamard", "my_reg", [(3,), (1,), (0,)])

    def test_reads_from(self):
        """Test ``reads_from``."""
        node = PauliPastCliffordNode("cx", "my_reg", [(0, 1), (4, 2)])
        assert node.reads_from() == {"my_reg": ({0, 1, 2, 4}, VirtualType.PAULI)}

    def test_writes_to(self):
        """Test ``writes_to`` method."""
        node = PauliPastCliffordNode("cx", "my_reg", [(0, 1), (4, 2)])
        assert node.writes_to() == {"my_reg": ({0, 1, 2, 4}, VirtualType.PAULI)}
