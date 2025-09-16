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
from qiskit.quantum_info import PauliLindbladMap, QubitSparsePauliList

from samplomatic.noise_source import StaticNoiseSource


class TestStaticNoiseSource:
    def test_dunders(self):
        """Test some dunders: contains, getitem and len."""
        assert len(StaticNoiseSource({})) == 0

        noise0 = PauliLindbladMap.from_list([("IXI", 0.5)])
        noise1 = PauliLindbladMap.from_list([("YZ", 1.0)])
        noise_source = StaticNoiseSource({"noise0": noise0, "noise1": noise1})

        assert len(noise_source) == 2
        assert "noise0" in noise_source
        assert "noise1" in noise_source
        assert "noise2" not in noise_source
        assert noise_source["noise0"] == noise0
        assert noise_source["noise1"] == noise1

        with pytest.raises(ValueError, match="'noise2' is not present"):
            noise_source["noise2"]

    def test_get_rates(self):
        """Test the `get_rates` method."""
        noise0 = PauliLindbladMap.from_list([("IXI", 0.5)])
        noise1 = PauliLindbladMap.from_list([("YZ", 1.0), ("IX", 0.3)])
        noise_source = StaticNoiseSource({"noise0": noise0, "noise1": noise1})

        assert np.array_equal(noise_source.get_rates("noise0"), [0.5])
        assert np.array_equal(noise_source.get_rates("noise1"), [1.0, 0.3])

        with pytest.raises(ValueError, match="'noise2' is not present"):
            noise_source.get_rates("noise2")

    def test_get_paulis(self):
        """Test the `get_paulis` method."""
        noise0 = PauliLindbladMap.from_list([("IXI", 0.5)])
        noise1 = PauliLindbladMap.from_list([("YZ", 1.0), ("IX", 0.3)])
        noise_source = StaticNoiseSource({"noise0": noise0, "noise1": noise1})

        assert noise_source.get_paulis("noise0") == QubitSparsePauliList.from_list(["IXI"])
        assert noise_source.get_paulis("noise1") == QubitSparsePauliList.from_list(["YZ", "IX"])

        with pytest.raises(ValueError, match="'noise2' is not present"):
            noise_source.get_paulis("noise2")
