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

from samplomatic.annotations import BasisTransform, BasisTransformMode, DecompositionMode


def test_construction():
    """Test that we can construct a BasisTransform."""
    basis_transform = BasisTransform()
    assert basis_transform.decomposition is DecompositionMode.RZSX
    assert basis_transform.mode is BasisTransformMode.MEASURE
    assert basis_transform.ref == "measure"

    basis_transform = BasisTransform(mode="prepare", ref="measure")
    assert basis_transform.mode is BasisTransformMode.PREPARE
    assert basis_transform.ref == "measure"


def test_eq():
    """Test equality."""
    assert BasisTransform() == BasisTransform()
    assert BasisTransform() != "hey"
    assert BasisTransform() != BasisTransform(decomposition="rzrx")
    assert BasisTransform() != BasisTransform(mode="prepare")
    assert BasisTransform() != BasisTransform(ref="ref")


def test_hash():
    """Test hash."""
    assert hash(BasisTransform()) == hash(BasisTransform())
    assert hash(BasisTransform()) != hash("hey")
    assert hash(BasisTransform()) != hash(BasisTransform(decomposition="rzrx"))
    assert hash(BasisTransform()) != hash(BasisTransform(mode="prepare"))
    assert hash(BasisTransform()) != hash(BasisTransform(ref="ref"))
