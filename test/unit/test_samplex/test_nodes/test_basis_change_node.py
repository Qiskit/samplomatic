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

"""Tests for ChangeBasisNode"""

import numpy as np
import pytest
from qiskit.circuit.library import HGate, IGate

from samplomatic.annotations import VirtualType
from samplomatic.samplex.nodes import ChangeBasisNode
from samplomatic.samplex.nodes.change_basis_node import (
    MEAS_PAULI_BASIS,
    PREP_PAULI_BASIS,
    BasisChange,
)
from samplomatic.tensor_interface import TensorInterface, TensorSpecification
from samplomatic.virtual_registers import PauliRegister, U2Register


class TestBasisChange:
    """Test the BasisChange class"""

    def test_construction(self):
        basis_change = BasisChange("ABC", PauliRegister([[0], [1], [2]]))
        assert basis_change.num_elements == 3
        assert basis_change.alphabet == ["A", "B", "C"]
        assert basis_change.action == PauliRegister([[0], [1], [2]])

    def test_construction_fails(self):
        """Test the construction fails when expected."""
        with pytest.raises(ValueError, match="basis elements is not equal .* symbols"):
            BasisChange("ABC", PauliRegister([[0], [1]]))

        with pytest.raises(ValueError, match="Expected the number of samples of 'action' to be 1"):
            BasisChange("ABC", PauliRegister([[0, 0], [1, 1], [2, 2]]))

    def test_get_transform(self):
        """Test the get_transform() method."""
        basis_change = BasisChange("ABC", PauliRegister([[0], [1], [2]]))
        assert basis_change.get_transform("CAABA") == PauliRegister([[2], [0], [0], [1], [0]])

    @pytest.mark.parametrize(
        ("symp", "basis"),
        [
            (2, np.array([[1.0, 1.0], [1.0, -1.0]]) / np.sqrt(2)),
            (3, np.array([[1.0, 1.0], [1.0j, -1.0j]]) / np.sqrt(2)),
        ],
    )
    def test_pauli_basis(self, symp, basis):
        prep_basis = PREP_PAULI_BASIS.get_transform([symp]).virtual_gates[0, 0]
        assert np.allclose(np.absolute(prep_basis.conj().T @ basis), np.eye(2))

        meas_basis = MEAS_PAULI_BASIS.get_transform([symp]).virtual_gates[0, 0]
        assert np.allclose(np.absolute(meas_basis @ basis), np.eye(2))


class TestChangeBasisNode:
    """Tests for ChangeBasisNode"""

    def test_construction(self):
        """Test attributes from construction."""
        basis_change = ChangeBasisNode("basis_change", MEAS_PAULI_BASIS, "measure", 3)
        assert basis_change.instantiates() == {"basis_change": (3, VirtualType.U2)}
        assert basis_change.outgoing_register_type is VirtualType.U2

    def test_sample(self):
        """Test evaluation of the node."""
        basis_change = ChangeBasisNode("basis_change", MEAS_PAULI_BASIS, "measure", 3)
        samplex_input = TensorInterface([TensorSpecification("measure", (3,), np.uint8)])
        registers = {}

        samplex_input.bind(measure=np.array([2, 2, 1], dtype=np.uint8))
        basis_change.sample(registers, None, samplex_input, 1)
        expected_register = U2Register(np.array([[HGate(), HGate(), IGate()]]).reshape(3, 1, 2, 2))
        assert registers["basis_change"] == expected_register

        samplex_input.bind(measure=np.array([2, 0, 0], dtype=np.uint8))
        basis_change.sample(registers, None, samplex_input, 13)
        expected_register = U2Register(np.array([[HGate(), IGate(), IGate()]]).reshape(3, 1, 2, 2))
        assert registers["basis_change"] == expected_register
        assert registers["basis_change"] == expected_register
