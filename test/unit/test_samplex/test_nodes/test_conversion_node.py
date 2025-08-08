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
from samplomatic.samplex.nodes import ConversionNode
from samplomatic.virtual_registers import PauliRegister, U2Register


def test_construction():
    """Test construction and basic attributes."""
    node = ConversionNode("existing", VirtualType.PAULI, "new", VirtualType.U2, 5, True)
    assert node.instantiates() == {"new": (5, VirtualType.U2)}
    assert not node.reads_from()
    assert node.removes() == {"existing"}
    assert not node.writes_to()
    assert node.outgoing_register_type is VirtualType.U2

    node = ConversionNode("existing", VirtualType.PAULI, "new", VirtualType.U2, 5, False)
    assert node.instantiates() == {"new": (5, VirtualType.U2)}
    assert node.reads_from() == {"existing": (set(range(5)), VirtualType.PAULI)}
    assert not node.removes()
    assert not node.writes_to()
    assert node.outgoing_register_type is VirtualType.U2


def test_construction_fails():
    """Test that construction fails when expected."""
    with pytest.raises(SamplexConstructionError, match="'foo'.* remove_existing was not .* true"):
        ConversionNode("foo", VirtualType.PAULI, "foo", VirtualType.U2, 10, True)


def test_validate_and_update_fails():
    """Test validation fails when expectations are not met."""
    node = ConversionNode("existing", VirtualType.PAULI, "new", VirtualType.PAULI, 5, True)
    with pytest.raises(SamplexConstructionError, match="'existing'.* 'u2'.*'pauli'"):
        node.validate_and_update({"existing": (5, VirtualType.U2)})

    node = ConversionNode("existing", VirtualType.PAULI, "new", VirtualType.U2, 6, True)
    with pytest.raises(SamplexConstructionError, match="size of 'existing' is 5 but should be 6"):
        node.validate_and_update({"existing": (5, VirtualType.PAULI)})


@pytest.mark.parametrize("remove", [True, False])
def test_evaluate(remove):
    """Test the evaluation method."""
    node = ConversionNode("existing", VirtualType.PAULI, "new", VirtualType.U2, 6, remove)
    registers = {"existing": PauliRegister.identity(5, 3)}
    node.evaluate(registers, np.empty(()))
    assert registers["new"] == U2Register.identity(5, 3)
    assert ("existing" not in registers) == remove

    registers = {"existing": PauliRegister(np.array([[0], [1], [2], [3], [0]]))}
    node.evaluate(registers, np.empty(()))
    expected_register = U2Register(
        np.array(
            [
                [np.diag([1, 1])],
                [np.diag([1, -1])],
                [np.diag([1, 1])[::-1]],
                [np.diag([-1j, 1j])[::-1]],
                [np.diag([1, 1])],
            ]
        ),
    )
    assert registers["new"] == expected_register
    assert ("existing" not in registers) == remove
