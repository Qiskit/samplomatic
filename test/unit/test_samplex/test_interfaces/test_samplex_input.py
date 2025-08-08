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

from samplomatic.exceptions import SamplexInputError
from samplomatic.samplex import ArrayInput, SamplexInput


def test_empty():
    """Test an empty output."""
    output = SamplexInput([])
    assert len(output) == 0
    assert not list(output)

    output.validate_and_update()


def test_construction():
    """Test construction and simple attributes."""

    input = SamplexInput(
        [
            ArrayInput("a", (5,), np.uint8, "desc_a"),
            ArrayInput("b", (3, 7), np.float32, "desc_b"),
        ],
    )

    assert len(input) == 2
    assert list(input) == ["a", "b"]
    assert "a" in input and "b" in input

    assert input["a"] is None
    assert input["b"] is None

    input.validate_and_update(a=np.arange(5, dtype=np.uint8), b=np.zeros((3, 7), np.float32))

    assert np.array_equal(input["a"], np.arange(5, dtype=np.uint8))
    assert np.array_equal(input["b"], np.zeros((3, 7), np.float32))


def test_exceptions():
    """Test exceptions."""

    input = SamplexInput(
        [
            ArrayInput("a", (5,), np.uint8, "desc_a"),
            ArrayInput("b", (3, 7), np.float32, "desc_b"),
        ],
    )
    b = np.zeros((3, 7), np.float32)

    with pytest.raises(SamplexInputError, match="requires an input named"):
        input.validate_and_update(b=b)

    with pytest.raises(SamplexInputError, match="expects an array"):
        input.validate_and_update(a=np.zeros((5,), np.float32), b=b)

    with pytest.raises(SamplexInputError, match="expects an array"):
        input.validate_and_update(a=np.zeros((7,), np.uint8), b=b)
