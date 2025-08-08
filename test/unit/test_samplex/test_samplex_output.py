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

from samplomatic.samplex import ArrayOutput, MetadataOutput, SamplexOutput


def test_empty():
    """Test an empty output."""
    output = SamplexOutput([], 10)
    assert len(output) == 0
    assert not list(output)


def test_construction():
    """Test construction and simple attributes."""

    output = SamplexOutput(
        [
            ArrayOutput("a", (5,), np.uint8, "desc_a"),
            MetadataOutput("b", "desc_b"),
            ArrayOutput("c", (3, 7), np.float32, "desc_c"),
        ],
        15,
    )

    assert output.num_samples == 15
    assert len(output) == 3
    assert list(output) == ["a", "b", "c"]
    assert "a" in output and "b" in output and "c" in output

    assert isinstance(output["a"], np.ndarray)
    assert output["a"].shape == (15, 5)
    assert output["a"].dtype == np.uint8

    assert isinstance(output["b"], dict)
    assert not output["b"]

    assert isinstance(output["c"], np.ndarray)
    assert output["c"].shape == (15, 3, 7)
    assert output["c"].dtype == np.float32
