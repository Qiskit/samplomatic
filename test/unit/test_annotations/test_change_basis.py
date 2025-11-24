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

from samplomatic.annotations import ChangeBasis, ChangeBasisMode, DecompositionMode


def test_construction():
    """Test that we can construct a ChangeBasis."""
    change_basis = ChangeBasis()
    assert change_basis.decomposition is DecompositionMode.RZSX
    assert change_basis.mode is ChangeBasisMode.MEASURE
    assert change_basis.ref == "measure"

    change_basis = ChangeBasis(mode="prepare", ref="measure")
    assert change_basis.mode is ChangeBasisMode.PREPARE
    assert change_basis.ref == "measure"


def test_eq():
    """Test equality."""
    assert ChangeBasis() == ChangeBasis()
    assert ChangeBasis() != "hey"
    assert ChangeBasis() != ChangeBasis(decomposition="rzrx")
    assert ChangeBasis() != ChangeBasis(mode="prepare")
    assert ChangeBasis() != ChangeBasis(ref="ref")


def test_hash():
    """Test hash."""
    assert hash(ChangeBasis()) == hash(ChangeBasis())
    assert hash(ChangeBasis()) != hash("hey")
    assert hash(ChangeBasis()) != hash(ChangeBasis(decomposition="rzrx"))
    assert hash(ChangeBasis()) != hash(ChangeBasis(mode="prepare"))
    assert hash(ChangeBasis()) != hash(ChangeBasis(ref="ref"))


def test_repr():
    """Test repr."""
    assert repr(ChangeBasis()) == "ChangeBasis(decomposition='rzsx', mode='measure', ref='measure')"
