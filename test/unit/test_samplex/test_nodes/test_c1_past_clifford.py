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


import numpy as np
import pytest

from samplomatic.exceptions import SamplexBuildError, SamplexRuntimeError
from samplomatic.samplex.nodes import C1PastCliffordNode
from samplomatic.virtual_registers import C1Register, VirtualType


class TestC1PastClifford:
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
