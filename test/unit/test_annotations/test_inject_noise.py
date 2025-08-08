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

from samplomatic.annotations import InjectNoise


def test_construction():
    """Test that we can construct a InjectNoise."""
    inject_noise = InjectNoise("its_name")
    assert inject_noise.ref == "its_name"


def test_eq():
    """Test equality."""
    assert InjectNoise("ref") == InjectNoise("ref")
    assert InjectNoise("ref") != "hey"
    assert InjectNoise("ref") != InjectNoise("another_ref")
    assert InjectNoise("ref") != InjectNoise("ref", "modifier_ref")


def test_hash():
    """Test hash."""
    assert hash(InjectNoise("ref")) == hash(InjectNoise("ref"))
    assert hash(InjectNoise("ref")) != hash("hey")
    assert hash(InjectNoise("ref")) != hash(InjectNoise("another_ref"))
    assert hash(InjectNoise("ref")) != hash(InjectNoise("ref", "modifier_ref"))
