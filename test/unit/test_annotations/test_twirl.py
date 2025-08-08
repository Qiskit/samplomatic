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

import pytest

from samplomatic.annotations import DecompositionMode, DressingMode, Twirl, VirtualType


def test_construction():
    """Test that we can construct a Twirl."""
    twirl = Twirl()

    assert twirl.group is VirtualType.PAULI
    assert twirl.decomposition is DecompositionMode.RZSX
    assert twirl.dressing is DressingMode.LEFT


def test_construction_raises():
    """Test that construction raises when expected."""
    with pytest.raises(ValueError, match="The group must be one of"):
        Twirl(group=VirtualType.Z2)


def test_eq():
    """Test equality."""
    assert Twirl() == Twirl()
    assert Twirl() != "hey"
    assert Twirl() != Twirl(decomposition="rzrx")
    assert Twirl() != Twirl(dressing="right")


def test_hash():
    """Test hash."""
    assert hash(Twirl()) == hash(Twirl())
    assert hash(Twirl()) != hash("hey")
    assert hash(Twirl()) != hash(Twirl(decomposition="rzrx"))
    assert hash(Twirl()) != hash(Twirl(dressing="right"))
