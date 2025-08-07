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

"""Tests for `get_annotation`"""

from qiskit.circuit import BoxOp, QuantumCircuit

from samplomatic.annotations import BasisTransform, InjectNoise, Twirl
from samplomatic.utils import get_annotation


def test_box_without_annotation():
    """Test `get_annotation` for box without annotation."""
    box = BoxOp(QuantumCircuit(2))
    assert get_annotation(box, Twirl) is None


def test_box_with_annotation():
    """Test `get_annotation` for box with annotations."""
    twirl = Twirl(dressing="right", decomposition="rzrx")
    basis_transform = BasisTransform(ref="ciao")
    box = BoxOp(QuantumCircuit(2), annotations=[twirl, basis_transform])

    assert get_annotation(box, Twirl) is twirl
    assert get_annotation(box, BasisTransform) is basis_transform
    assert get_annotation(box, InjectNoise) is None
