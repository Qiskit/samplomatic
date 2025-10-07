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


import numpy as np
import pytest
from qiskit.circuit.library import HGate, SXGate, XGate

from samplomatic.annotations import VirtualType
from samplomatic.exceptions import SamplexConstructionError
from samplomatic.samplex.nodes import CombineRegistersNode
from samplomatic.virtual_registers import PauliRegister, U2Register


def test_inserting_identities():
    """Test inserting identities in a register using a ``CombineRegistersNode``."""
    registers = {"reg": PauliRegister([[0, 1, 2, 3], [1, 2, 3, 0]])}
    node = CombineRegistersNode(
        VirtualType.PAULI, "larger_reg", 3, {"reg": [(0, 1), (0, 2), VirtualType.PAULI]}
    )
    assert node.outgoing_register_type is VirtualType.PAULI

    node.evaluate(registers, np.empty(()))
    assert registers["larger_reg"].virtual_gates.tolist() == [
        [0, 1, 2, 3],
        [0, 0, 0, 0],
        [1, 2, 3, 0],
    ]


def test_swapping_two_subsystems():
    """Test swapping subsystems in a register using a ``CombineRegistersNode``."""
    registers = {"reg": PauliRegister([[0, 1, 2, 3], [1, 2, 3, 0]])}
    node = CombineRegistersNode(
        VirtualType.PAULI, "swapped_reg", 2, {"reg": [(0, 1), (1, 0), VirtualType.PAULI]}
    )
    assert node.outgoing_register_type is VirtualType.PAULI

    node.evaluate(registers, np.empty(()))
    assert registers["swapped_reg"].virtual_gates.tolist() == [[1, 2, 3, 0], [0, 1, 2, 3]]


def test_tensoring():
    """Test tensoring two subsystems using a ``CombineRegistersNode``"""
    registers = {
        "reg_1q": PauliRegister([[0, 1, 2, 3]]),
        "reg_2q": PauliRegister([[1, 1, 1, 1], [2, 2, 2, 2]]),
    }

    operands = {
        "reg_1q": [(0,), (1,), VirtualType.PAULI],
        "reg_2q": [(0, 1), (0, 2), VirtualType.PAULI],
    }
    node = CombineRegistersNode(VirtualType.PAULI, "tensored_reg", 3, operands)
    node.evaluate(registers, np.empty(()))

    expected = [[1, 1, 1, 1], [0, 1, 2, 3], [2, 2, 2, 2]]
    assert registers["tensored_reg"].virtual_gates.tolist() == expected


def test_slicing():
    """Test slicing registers using a ``CombineRegistersNode``"""
    registers = {
        "reg1": PauliRegister([[0, 0, 0, 0], [3, 3, 3, 3]]),
        "reg2": PauliRegister([[1, 1, 1, 1], [2, 2, 2, 2]]),
    }

    operands = {
        "reg1": [(0,), (0,), VirtualType.PAULI],
        "reg2": [(1,), (0,), VirtualType.PAULI],
    }
    node = CombineRegistersNode(VirtualType.PAULI, "sliced", 1, operands)
    node.evaluate(registers, np.empty(()))

    expected = [[2, 2, 2, 2]]
    assert registers["sliced"].virtual_gates.tolist() == expected


def test_combine_three_registers_of_different_sizes():
    """Test combining three registers of different size using a ``CombineRegistersNode``."""
    registers = {
        "reg_1q": PauliRegister([[0, 1, 2, 3]]),
        "reg_2q": PauliRegister([[1, 1, 1, 1], [2, 2, 2, 2]]),
        "reg_3q": PauliRegister([[3, 3, 3, 3], [2, 2, 2, 2], [1, 1, 1, 1]]),
    }

    operands0 = {
        "reg_1q": [(0,), (1,), VirtualType.PAULI],
        "reg_2q": [(0, 1), (1, 2), VirtualType.PAULI],
    }
    node = CombineRegistersNode(VirtualType.PAULI, "combined_reg0", 3, operands0)
    node.evaluate(registers, np.empty(()))
    expected = [[0, 0, 0, 0], [1, 0, 3, 2], [2, 2, 2, 2]]
    assert registers["combined_reg0"].virtual_gates.tolist() == expected

    operands1 = {
        "combined_reg0": [(0, 1, 2), (0, 1, 2), VirtualType.PAULI],
        "reg_3q": [(0, 1, 2), (2, 0, 1), VirtualType.PAULI],
    }
    node = CombineRegistersNode(VirtualType.PAULI, "combined_reg1", 3, operands1)
    node.evaluate(registers, np.empty(()))
    expected = [[2, 2, 2, 2], [0, 1, 2, 3], [1, 1, 1, 1]]
    assert registers["combined_reg1"].virtual_gates.tolist() == expected

    operands2 = {
        "reg_1q": [(0,), (1,), VirtualType.PAULI],
        "reg_2q": [(0, 1), (1, 2), VirtualType.PAULI],
        "reg_3q": [(0, 1, 2), (2, 0, 1), VirtualType.PAULI],
    }
    node = CombineRegistersNode(VirtualType.PAULI, "combined_reg2", 3, operands2)
    assert node.outgoing_register_type is VirtualType.PAULI
    node.evaluate(registers, np.empty(()))
    expected = [[2, 2, 2, 2], [0, 1, 2, 3], [1, 1, 1, 1]]
    assert registers["combined_reg2"].virtual_gates.tolist() == expected

    expected_keys = {
        "reg_1q",
        "reg_2q",
        "reg_3q",
        "combined_reg1",
        "combined_reg1",
        "combined_reg2",
    }
    assert expected_keys.difference(registers.keys()) == set()


def test_combine_three_registers_in_correct_order():
    """Test that ``CombineRegistersNode`` combines registers in standard operator order."""
    h_mat = HGate().to_matrix()
    sx_mat = SXGate().to_matrix()

    registers = {
        "u2_0": U2Register([[h_mat]]),
        "u2_1": U2Register([[sx_mat]]),
        "u2_2": U2Register([[h_mat]]),
    }

    operands = {"u2_0": [(0,), (0,), VirtualType.U2], "u2_1": [(0,), (0,), VirtualType.U2]}
    node = CombineRegistersNode(VirtualType.U2, "h.sx", 1, operands)
    node.evaluate(registers, np.empty(()))
    assert registers["h.sx"].virtual_gates[0][0].tolist() == np.dot(h_mat, sx_mat).tolist()
    assert node.outgoing_register_type is VirtualType.U2

    operands = {"u2_1": [(0,), (0,), VirtualType.U2], "u2_0": [(0,), (0,), VirtualType.U2]}
    node = CombineRegistersNode(VirtualType.U2, "h.sx", 1, operands)
    node.evaluate(registers, np.empty(()))
    assert registers["h.sx"].virtual_gates[0][0].tolist() == np.dot(sx_mat, h_mat).tolist()


def test_convert_and_combine_registers():
    """Test that ``CombineRegistersNode`` converts the register type when possible."""
    h_mat = HGate().to_matrix()
    x_mat = XGate().to_matrix()

    registers = {
        "u2_0": U2Register([[h_mat]]),
        "u2_1": PauliRegister([[2]]),
    }

    operands = {"u2_0": [(0,), (0,), VirtualType.U2], "u2_1": [(0,), (0,), VirtualType.PAULI]}
    node = CombineRegistersNode(VirtualType.U2, "h.x", 1, operands)
    node.evaluate(registers, np.empty(()))
    assert registers["h.x"].virtual_gates[0][0].tolist() == np.dot(h_mat, x_mat).tolist()
    assert node.outgoing_register_type is VirtualType.U2


def test_raises():
    """Test that the ``CombineRegistersNode`` raises."""
    with pytest.raises(SamplexConstructionError, match=r"Output .+ 'reg' .+ \[0, 0\]"):
        CombineRegistersNode(
            VirtualType.PAULI, "combined_reg", 1, {"reg": [(0,), (1,), VirtualType.PAULI]}
        )

    node = CombineRegistersNode(
        VirtualType.PAULI, "combined_reg", 1, {"reg": [(1,), (0,), VirtualType.PAULI]}
    )
    with pytest.raises(SamplexConstructionError, match="at least 2 subsystems for read access"):
        node.validate_and_update({"reg": (1, VirtualType.PAULI)})

    with pytest.raises(SamplexConstructionError, match="wrong shape"):
        CombineRegistersNode(
            VirtualType.PAULI, "combined_reg", 1, {"reg": [(1, 0), (0,), VirtualType.PAULI]}
        )

    with pytest.raises(SamplexConstructionError, match="at least one"):
        CombineRegistersNode(VirtualType.PAULI, "combined_reg", 1, {})

    operands = {
        "pauli_reg": [(0,), (0,), VirtualType.PAULI],
        "u2_reg": [(0,), (0,), VirtualType.U2],
    }
    node = CombineRegistersNode(VirtualType.PAULI, "combined_reg", 1, operands)
    with pytest.raises(
        SamplexConstructionError, match=r"`u2_reg` to be convertable to type 'pauli"
    ):
        node.validate_and_update(
            {"pauli_reg": (1, VirtualType.PAULI), "u2_reg": (1, VirtualType.U2)}
        )
