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

from samplomatic.annotations import Tag


def test_eq():
    """Test equality."""
    assert Tag() == Tag()
    assert Tag(ref="a") == Tag(ref="a")
    assert Tag(ref="a") != Tag(ref="b")
    assert Tag(ref="a") != Tag()
    assert Tag() != "hey"


def test_hash():
    """Test hash."""
    assert hash(Tag()) == hash(Tag())
    assert hash(Tag(ref="a")) == hash(Tag(ref="a"))
    assert hash(Tag(ref="a")) != hash(Tag())
    assert hash(Tag()) != hash("hey")


def test_repr():
    """Test repr."""
    assert repr(Tag()) == "Tag()"
    assert repr(Tag(ref="a")) == "Tag(ref='a')"
