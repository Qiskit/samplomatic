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


from itertools import product

import pytest
from qiskit.circuit.library import CXGate, CZGate, ECRGate
from qiskit.quantum_info import Clifford

from samplomatic.samplex.nodes.c1_past_clifford_node import C1_PAST_CLIFFORD_LOOKUP_TABLES
from samplomatic.virtual_registers.c1_register import C1_TO_TABLEAU


class TestLookupTables:
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
