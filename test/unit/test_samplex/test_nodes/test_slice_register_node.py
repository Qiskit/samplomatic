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

from samplomatic.annotations import VirtualType
from samplomatic.exceptions import SamplexConstructionError
from samplomatic.samplex.nodes import SliceRegisterNode
from samplomatic.virtual_registers import PauliRegister


def test_no_slice():
    """Test that slice and permutes returns the original register in the trivial case."""
    registers = {"reg_in": PauliRegister([[0, 1, 2, 3], [1, 2, 3, 0]])}
    node = SliceRegisterNode(
        VirtualType.PAULI,
        VirtualType.PAULI,
        "reg_in",
        "reg_out",
        [0, 1],
    )

    node.evaluate(registers, np.empty(()))
    expected = registers["reg_in"].virtual_gates.tolist()
    assert registers["reg_out"].virtual_gates.tolist() == expected
    assert node.outgoing_register_type is VirtualType.PAULI


def test_swapping_two_subsystems():
    """Test swapping subsystems in a register using a ``SliceRegisterNode``."""
    registers = {"reg_in": PauliRegister([[0, 1, 2, 3], [1, 2, 3, 0]])}
    node = SliceRegisterNode(
        VirtualType.PAULI,
        VirtualType.PAULI,
        "reg_in",
        "reg_out",
        [1, 0],
    )

    node.evaluate(registers, np.empty(()))
    expected = registers["reg_in"].virtual_gates.tolist()[::-1]
    assert registers["reg_out"].virtual_gates.tolist() == expected
    assert node.outgoing_register_type is VirtualType.PAULI


@pytest.mark.parametrize("slice_idxs", [[0, 1], [1, 2], [0, 2]])
def test_slicing(slice_idxs):
    """Test slicing registers using a ``SliceRegisterNode``"""
    registers = {"reg_in": PauliRegister([[0, 1, 2, 3], [1, 2, 3, 0], [2, 3, 0, 1]])}
    node = SliceRegisterNode(
        VirtualType.PAULI,
        VirtualType.PAULI,
        "reg_in",
        "reg_out",
        slice_idxs,
    )

    node.evaluate(registers, np.empty(()))
    expected = registers["reg_in"].virtual_gates[slice_idxs].tolist()
    assert registers["reg_out"].virtual_gates.tolist() == expected
    assert node.outgoing_register_type is VirtualType.PAULI


@pytest.mark.parametrize("slice_idxs", [[1, 0], [2, 1], [2, 0]])
def test_slicing_and_permuting(slice_idxs):
    """Test slicing and permuting at the same time a register using a ``SliceRegisterNode``."""
    registers = {"reg_in": PauliRegister([[0, 1, 2, 3], [1, 2, 3, 0], [2, 3, 0, 1]])}
    node = SliceRegisterNode(
        VirtualType.PAULI,
        VirtualType.PAULI,
        "reg_in",
        "reg_out",
        slice_idxs,
    )

    node.evaluate(registers, np.empty(()))
    expected = registers["reg_in"].virtual_gates[slice_idxs].tolist()
    assert registers["reg_out"].virtual_gates.tolist() == expected


def test_raises():
    """Test that the ``SliceRegisterNode`` raises."""
    with pytest.raises(SamplexConstructionError, match="single axes"):
        node = SliceRegisterNode(
            VirtualType.PAULI,
            VirtualType.PAULI,
            "reg_in",
            "reg_out",
            [[0, 1], [2, 3]],
        )

    node = SliceRegisterNode(
        VirtualType.U2,
        VirtualType.PAULI,
        "reg_in",
        "reg_out",
        [0, 1],
    )
    with pytest.raises(SamplexConstructionError, match="convertable"):
        node.validate_and_update({"reg_in": (2, VirtualType.U2)})
