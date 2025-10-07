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

from samplomatic.samplex import SamplexOutput
from samplomatic.tensor_interface import TensorSpecification


class TestSamplexOutput:
    """Test ``SamplexOutput``."""

    def test_empty(self):
        """Test an empty output."""
        output = SamplexOutput([])
        assert len(output) == 0
        assert not list(output)
        assert not output.metadata

    def test_construction(self):
        """Test construction and simple attributes."""
        output = SamplexOutput(
            [
                TensorSpecification("a", (5,), np.uint8, "desc_a"),
                TensorSpecification("c", (3, 7), np.float32, "desc_c"),
            ]
        )

        assert len(output) == 2
        assert list(output) == ["a", "c"]
        assert "a" in output and "c" in output
        assert len(output.metadata) == 0

        assert isinstance(output["a"], np.ndarray)
        assert output["a"].shape == (5,)
        assert output["a"].dtype == np.uint8

        assert isinstance(output["c"], np.ndarray)
        assert output["c"].shape == (3, 7)
        assert output["c"].dtype == np.float32
