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


from qiskit.quantum_info import Clifford

from samplomatic.tables.c1_tables import C1_TO_TABLEAU


def test_tableaus():
    """Test that the tableaus are correct."""
    h = Clifford.from_label("H")
    g = h @ Clifford.from_label("S")
    for idx, tableau in enumerate(C1_TO_TABLEAU):
        i, j, k = idx // 8 % 3, idx // 4 % 2, idx % 4
        g_pow = g.power(i) if i > 0 else Clifford.from_label("I")
        h_pow = h.power(j) if j > 0 else Clifford.from_label("I")
        assert g_pow @ h_pow @ Clifford.from_label("IZXY"[k]) == Clifford(tableau)
