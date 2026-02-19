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


from itertools import product

import numpy as np
import pytest
from qiskit.circuit.library import CXGate, CZGate, ECRGate, HGate
from qiskit.quantum_info import Clifford

from samplomatic.exceptions import SamplexBuildError, SamplexRuntimeError
from samplomatic.samplex.nodes import C1PastCliffordNode
from samplomatic.samplex.nodes.c1_past_clifford_node import C1_PAST_CLIFFORD_LOOKUP_TABLES
from samplomatic.virtual_registers import C1Register, VirtualType
from samplomatic.virtual_registers.c1_register import C1_TO_TABLEAU


class TestLookupTables:
    @pytest.mark.parametrize("op_class", [HGate])
    def test_1q_gate_tables(self, op_class):
        """Test the lookup tables for one-qubit gates."""
        op = op_class()
        gate_cliff = Clifford(op)
        gate_inv = gate_cliff.adjoint()
        table = C1_PAST_CLIFFORD_LOOKUP_TABLES[op.name]

        for c1_idx in range(24):
            c1_cliff = Clifford(C1_TO_TABLEAU[c1_idx], False)
            result = gate_inv.dot(c1_cliff).dot(gate_cliff)
            expected = Clifford(C1_TO_TABLEAU[table[c1_idx, 0]], False)

            assert result == expected, (
                f"C1[{c1_idx}] through {op.name}: Table says C1[{table[c1_idx, 0]}], "
                f"but Qiskit gives a different result."
            )

    @pytest.mark.parametrize("op_class", [CXGate, CZGate, ECRGate])
    def test_2q_gate_tables(self, op_class):
        """Test the lookup tables for two-qubit gates."""
        op = op_class()
        gate_cliff = Clifford(op)
        gate_inv = gate_cliff.adjoint()
        table = C1_PAST_CLIFFORD_LOOKUP_TABLES[op.name]

        for c0, c1 in product(range(24), repeat=2):
            cliff0 = Clifford(C1_TO_TABLEAU[c0], False)
            cliff1 = Clifford(C1_TO_TABLEAU[c1], False)
            cliff_2q = cliff1.tensor(cliff0)
            result = gate_inv.dot(cliff_2q).dot(gate_cliff)

            if table[c0, c1, 0] == -1:
                # Verify result does not factorize into C1 ⊗ C1
                tab = result.tableau
                has_cross = (
                    tab[0, 1]
                    or tab[0, 3]
                    or tab[1, 0]
                    or tab[1, 2]
                    or tab[2, 1]
                    or tab[2, 3]
                    or tab[3, 0]
                    or tab[3, 2]
                )
                assert has_cross, (
                    f"({c0}, {c1}) through {op.name}: Table says non-local, "
                    f"but result appears local."
                )
            else:
                expected_0 = Clifford(C1_TO_TABLEAU[table[c0, c1, 0]], False)
                expected_1 = Clifford(C1_TO_TABLEAU[table[c0, c1, 1]], False)
                expected_2q = expected_1.tensor(expected_0)
                assert result == expected_2q, (
                    f"({c0}, {c1}) through {op.name}: Table says "
                    f"({table[c0, c1, 0]}, {table[c0, c1, 1]}), "
                    f"but Qiskit gives a different result."
                )


class TestC1PastClifford:
    def test_one_qubit_gate(self):
        """Test propagating C1 register past a one-qubit Clifford gate."""
        node = C1PastCliffordNode("h", "my_reg", [(3,), (1,), (0,)])

        reg = C1Register(np.array([[0, 1], [4, 2], [2, 0], [3, 5]], dtype=np.uint8))
        node.evaluate({"my_reg": reg}, np.empty(()))

        # H conjugation: 0→0, 1→2, 2→1, 3→3, 4→4, 5→6
        # Subsystem 3: [3, 5] → [3, 6]
        # Subsystem 1: [4, 2] → [4, 1]
        # Subsystem 0: [0, 1] → [0, 2]
        assert reg.virtual_gates.tolist() == [[0, 2], [4, 1], [2, 0], [3, 6]]
        assert node.outgoing_register_type is VirtualType.C1

    def test_cx_gate(self):
        """Test propagating C1 register past a controlled-X gate."""
        node = C1PastCliffordNode("cx", "my_reg", [(0, 1)])
        assert node.outgoing_register_type is VirtualType.C1

        # Use Pauli subgroup inputs (C1 indices 0-3) which always remain local
        # CX Pauli table: (0,0)→(0,0), (2,0)→(2,2), (1,3)→(0,3)
        reg = C1Register(np.array([[0, 2, 1], [0, 0, 3]], dtype=np.uint8))
        node.evaluate({"my_reg": reg}, np.empty(()))

        assert reg.virtual_gates.tolist() == [[0, 2, 0], [0, 2, 3]]

    def test_cx_gate_non_pauli(self):
        """Test propagating non-Pauli C1 elements past a controlled-X gate."""
        node = C1PastCliffordNode("cx", "my_reg", [(0, 1)])

        # (22,13)→(23,15), (20,14)→(20,14)
        reg = C1Register(np.array([[22, 20], [13, 14]], dtype=np.uint8))
        node.evaluate({"my_reg": reg}, np.empty(()))

        assert reg.virtual_gates.tolist() == [[23, 20], [15, 14]]

    def test_cz_gate(self):
        """Test propagating C1 register past a controlled-Z gate."""
        node = C1PastCliffordNode("cz", "my_reg", [(0, 1)])
        assert node.outgoing_register_type is VirtualType.C1

        # CZ Pauli table: (0,0)→(0,0), (2,3)→(3,2), (1,2)→(0,2)
        reg = C1Register(np.array([[0, 2, 1], [0, 3, 2]], dtype=np.uint8))
        node.evaluate({"my_reg": reg}, np.empty(()))

        assert reg.virtual_gates.tolist() == [[0, 3, 0], [0, 2, 2]]

    def test_cz_gate_non_pauli(self):
        """Test propagating non-Pauli C1 elements past a controlled-Z gate."""
        node = C1PastCliffordNode("cz", "my_reg", [(0, 1)])

        # (22,20)→(22,21), (20,22)→(21,22)
        reg = C1Register(np.array([[22, 20], [20, 22]], dtype=np.uint8))
        node.evaluate({"my_reg": reg}, np.empty(()))

        assert reg.virtual_gates.tolist() == [[22, 21], [21, 22]]

    def test_ecr_gate(self):
        """Test propagating C1 register past an ECR gate."""
        node = C1PastCliffordNode("ecr", "my_reg", [(0, 1)])
        assert node.outgoing_register_type is VirtualType.C1

        # ECR Pauli table: (0,0)→(0,0), (2,3)→(2,3), (1,2)→(1,2)
        reg = C1Register(np.array([[0, 2, 1], [0, 3, 2]], dtype=np.uint8))
        node.evaluate({"my_reg": reg}, np.empty(()))

        assert reg.virtual_gates.tolist() == [[0, 2, 1], [0, 3, 2]]

    def test_ecr_gate_non_pauli(self):
        """Test propagating non-Pauli C1 elements past an ECR gate."""
        node = C1PastCliffordNode("ecr", "my_reg", [(0, 1)])

        # (20,12)→(21,12), (22,13)→(23,13)
        reg = C1Register(np.array([[20, 22], [12, 13]], dtype=np.uint8))
        node.evaluate({"my_reg": reg}, np.empty(()))

        assert reg.virtual_gates.tolist() == [[21, 23], [12, 13]]

    def test_invalid_input_errors(self):
        """Test that non-local conjugation raises SamplexRuntimeError."""
        node = C1PastCliffordNode("cx", "my_reg", [(0, 1)])
        # c0=4 (H), c1=0 (I) does not stay local under CX conjugation
        reg = C1Register(np.array([[4], [0]], dtype=np.uint8))

        with pytest.raises(SamplexRuntimeError, match="did not remain local"):
            node.evaluate({"my_reg": reg}, np.empty(()))

    def test_init_error(self):
        """Test init error."""
        with pytest.raises(SamplexBuildError, match=", found hadamard."):
            C1PastCliffordNode("hadamard", "my_reg", [(3,), (1,), (0,)])

    def test_equality(self, dummy_evaluation_node):
        node = C1PastCliffordNode("cx", "my_reg", [(0, 3), (1, 4), (2, 5)])
        assert node == node
        assert node == C1PastCliffordNode("cx", "my_reg", [(0, 3), (1, 4), (2, 5)])
        assert node != dummy_evaluation_node()
        assert node != C1PastCliffordNode("cx", "my_reg", [(3, 0), (1, 4), (2, 5)])
        assert node != C1PastCliffordNode("cx", "my_other_reg", [(0, 3), (1, 4), (2, 5)])
        assert node != C1PastCliffordNode("ecr", "my_reg", [(0, 3), (1, 4), (2, 5)])

    def test_reads_from(self):
        """Test ``reads_from``."""
        node = C1PastCliffordNode("cx", "my_reg", [(0, 1), (4, 2)])
        assert node.reads_from() == {"my_reg": ({0, 1, 2, 4}, VirtualType.C1)}

    def test_writes_to(self):
        """Test ``writes_to`` method."""
        node = C1PastCliffordNode("cx", "my_reg", [(0, 1), (4, 2)])
        assert node.writes_to() == {"my_reg": ({0, 1, 2, 4}, VirtualType.C1)}
