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

from samplomatic.annotations import DecompositionMode, DressingMode, InjectLocalClifford


def test_construction():
    """Test that we can construct a InjectLocalClifford."""
    inject_clifford = InjectLocalClifford("my_clifford")
    assert inject_clifford.decomposition is DecompositionMode.RZSX
    assert inject_clifford.dressing is DressingMode.LEFT
    assert inject_clifford.ref == "my_clifford"

    inject_clifford = InjectLocalClifford("my_clifford", dressing="right")
    assert inject_clifford.dressing is DressingMode.RIGHT
    assert inject_clifford.ref == "my_clifford"


def test_eq():
    """Test equality."""
    inject_clifford = InjectLocalClifford("my_clifford")
    assert inject_clifford == InjectLocalClifford("my_clifford")
    assert inject_clifford != "hey"
    assert inject_clifford != InjectLocalClifford("my_clifford", decomposition="rzrx")
    assert inject_clifford != InjectLocalClifford("my_clifford", dressing="right")


def test_hash():
    """Test hash."""
    inject_clifford = InjectLocalClifford("my_clifford")
    assert hash(inject_clifford) == hash(InjectLocalClifford("my_clifford"))
    assert hash(inject_clifford) != hash("hey")
    assert hash(inject_clifford) != hash(InjectLocalClifford("my_clifford", decomposition="rzrx"))
    assert hash(inject_clifford) != hash(InjectLocalClifford("my_clifford", dressing="right"))


def test_repr():
    """Test repr."""
    assert (
        repr(InjectLocalClifford("my_clifford"))
        == "InjectLocalClifford(ref='my_clifford', decomposition='rzsx', dressing='left')"
    )
