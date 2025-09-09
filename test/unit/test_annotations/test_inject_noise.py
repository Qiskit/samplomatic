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

from qiskit.quantum_info import QubitSparsePauliList

from samplomatic.annotations import InjectNoise


def test_construction():
    """Test that we can construct a InjectNoise."""
    inject_noise = InjectNoise("its_name", model := QubitSparsePauliList.from_list(["XX"]))
    assert inject_noise.ref == "its_name"
    assert inject_noise.model == model
    assert inject_noise.modifier_ref == ""


def test_eq():
    """Test equality."""
    model0 = QubitSparsePauliList.from_list(["XX"])
    model1 = QubitSparsePauliList.from_sparse_list([("XX", (0, 1))], 3)
    assert InjectNoise("ref", model0) == InjectNoise("ref", model0)
    assert InjectNoise("ref", model0) != InjectNoise("another_ref", model0)
    assert InjectNoise("ref", model0) != InjectNoise("ref", model1)
    assert InjectNoise("ref", model0) != InjectNoise("ref", model0, "modifier_ref")


def test_hash():
    """Test hash."""
    model0 = QubitSparsePauliList.from_list(["XX"])
    model1 = QubitSparsePauliList.from_sparse_list([("XX", (0, 1))], 3)
    assert hash(InjectNoise("ref", model0)) == hash(InjectNoise("ref", model0))
    assert hash(InjectNoise("ref", model0)) == hash(InjectNoise("ref", model1))
    assert hash(InjectNoise("ref", model0)) != hash(InjectNoise("another_ref", model0))
    assert hash(InjectNoise("ref", model0)) != hash(InjectNoise("ref", model0, "modifier_ref"))
