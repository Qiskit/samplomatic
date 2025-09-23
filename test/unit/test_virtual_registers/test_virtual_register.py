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

"""Test the VirtualRegister base class"""

import numpy as np
import pytest

from samplomatic.annotations import VirtualType
from samplomatic.exceptions import VirtualGateError
from samplomatic.virtual_registers import VirtualRegister


class DummyRegister(VirtualRegister):
    """Dummy virtual register implementation to test the base class in isolation."""

    GATE_SHAPE = (3,)
    DTYPE = np.float64
    SUBSYSTEM_SIZE = 1

    @classmethod
    def identity(cls, num_subsystems, num_samples):
        arr = np.zeros((num_subsystems, num_samples, 3), dtype=np.float64)
        arr[..., 1] = 1
        arr[..., 2] = 2
        return cls(arr)


def test_construction_and_attributes():
    """Test that attributes are correct after successful construction."""
    reg = DummyRegister(arr := np.linspace(0, 1, 2 * 4 * 3).reshape((2, 4, 3)))

    assert reg.shape == (2, 4)
    assert reg.size == 8
    assert reg.num_samples == 4
    assert reg.num_subsystems == 2
    assert np.allclose(reg.virtual_gates, arr)


def test_failed_construction():
    """Test that the constructor fails when expected."""
    with pytest.raises(VirtualGateError, match="2 leading axes followed by"):
        DummyRegister(np.empty(()))

    with pytest.raises(VirtualGateError, match="2 leading axes followed by"):
        DummyRegister(np.empty((5,)))

    with pytest.raises(VirtualGateError, match="2 leading axes followed by"):
        DummyRegister(np.empty((5, 6)))

    with pytest.raises(VirtualGateError, match="2 leading axes followed by"):
        DummyRegister(np.empty((5, 6, 3, 1)))

    with pytest.raises(VirtualGateError, match=r"end with \(3,\)"):
        DummyRegister(np.empty((5, 6, 4)))


def test_empty_construction():
    """Test the empty() class method constructor."""
    reg = DummyRegister.empty(5, 6)
    assert reg.num_samples == 6
    assert reg.num_subsystems == 5


def test_identity_construction():
    """Test the empty() class method constructor."""
    reg = DummyRegister.identity(8, 6)
    assert reg.num_samples == 6
    assert reg.num_subsystems == 8
    assert np.allclose(reg.virtual_gates[2, 3, :], [0, 1, 2])


def test_copy():
    """Test the copy() method."""
    reg = DummyRegister.identity(4, 5)
    reg_copy = reg.copy()

    assert reg == reg_copy
    assert reg is not reg_copy


def test_equality():
    """Test the equality dunder."""
    reg1 = DummyRegister(np.linspace(0, 1, 2 * 4 * 3).reshape((2, 4, 3)))
    reg2 = DummyRegister(np.linspace(0, 1, 2 * 4 * 3).reshape((2, 4, 3)))
    reg3 = DummyRegister(np.linspace(0, 2, 2 * 4 * 3).reshape((2, 4, 3)))

    assert reg1 != 42
    assert reg1 == reg1
    assert reg1 == reg2
    assert reg2 != reg3
    assert reg1 != reg3
    assert reg3 == reg3


def test_getitem():
    """Test the getitem dunder."""
    reg = DummyRegister(arr := np.linspace(0, 1, 2 * 4 * 3).reshape((2, 4, 3)))

    assert isinstance(reg[:], DummyRegister)
    assert reg[:] == reg
    assert reg[:] is not reg
    assert reg[:1] == DummyRegister(arr[:1])
    assert reg[[1]] == DummyRegister(arr[[1]])
    assert reg[1::2] == DummyRegister(arr[1::2])


def test_getitem_returns_view():
    """Test the getitem dunder."""
    reg = DummyRegister(np.linspace(0, 1, 5 * 4 * 3).reshape((5, 4, 3)))
    reg_slice = reg[2:4]
    reg_slice.virtual_gates[0, 0, 0] = 18.0
    assert np.isclose(reg.virtual_gates[2, 0, 0], 18)

    # with fancy indexing, we DO NOT get a view back
    reg = DummyRegister(np.linspace(0, 1, 5 * 4 * 3).reshape((5, 4, 3)))
    reg_slice = reg[[2, 3, 4]]
    reg_slice.virtual_gates[0, 0, 0] = 18.0
    assert not np.isclose(reg.virtual_gates[2, 0, 0], 18)


def test_getitem_raises():
    """Test that getitem raises when expected."""
    with pytest.raises(VirtualGateError, match="only be sliced along their first axis."):
        DummyRegister.empty(4, 5)[:, :]

    with pytest.raises(VirtualGateError, match="Slicing to singletons is not supported."):
        DummyRegister.empty(4, 5)[0]


def test_setitem():
    """Test the getitem dunder."""
    reg = DummyRegister(arr := np.linspace(0, 1, 2 * 4 * 3).reshape((2, 4, 3)))
    reg[0, 0] = [5, 6, 7]
    assert np.allclose(reg.virtual_gates[0, 0, :], [5, 6, 7])
    assert np.allclose(reg.virtual_gates[0, 1, :], arr[0, 1, :])

    reg = DummyRegister(arr := np.linspace(0, 1, 5 * 4 * 3).reshape((5, 4, 3)))
    reg[[2, 3]] = [5, 6, 7]
    assert np.allclose(reg.virtual_gates[2, 2, :], [5, 6, 7])
    assert np.allclose(reg.virtual_gates[3, 1, :], [5, 6, 7])
    assert np.allclose(reg.virtual_gates[0, 1, :], arr[0, 1, :])


def test_setitem_from_register():
    """Test the getitem dunder."""
    reg = DummyRegister(arr := np.linspace(0, 1, 2 * 4 * 3).reshape((2, 4, 3)))
    reg[0, 0] = DummyRegister([[[5, 6, 7]]])
    assert np.allclose(reg.virtual_gates[0, 0, :], [5, 6, 7])
    assert np.allclose(reg.virtual_gates[0, 1, :], arr[0, 1, :])

    reg = DummyRegister(arr := np.linspace(0, 1, 5 * 4 * 3).reshape((5, 4, 3)))
    reg[[2, 3]] = DummyRegister([[[5, 6, 7], [5, 6, 7], [5, 6, 7], [5, 6, 7]]] * 2)
    assert np.allclose(reg.virtual_gates[2, 2, :], [5, 6, 7])
    assert np.allclose(reg.virtual_gates[3, 1, :], [5, 6, 7])
    assert np.allclose(reg.virtual_gates[0, 1, :], arr[0, 1, :])


def test_type_registration():
    """Test the type registration system."""
    with pytest.raises(ValueError, match="VirtualRegister.TYPE must be a VirtualType"):

        class _(DummyRegister):
            TYPE = object()

    with pytest.raises(ValueError, match="TYPE 'pauli has already been registered"):

        class _(DummyRegister):
            TYPE = VirtualType.PAULI
