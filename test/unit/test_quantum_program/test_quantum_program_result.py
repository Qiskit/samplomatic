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


import numpy as np

from samplomatic.quantum_program import QuantumProgramItemResult, QuantumProgramResult


class TestQuantumProgramResult:
    """Tests the ``QuantumProgramResult`` class."""

    def test_result(self):
        """Test initializing a ``QuantumProgramResult`` object."""
        data = [
            {
                "alpha": np.random.random((1, 2, 3)).astype(bool),
                "beta": np.random.random((1, 2, 3)).astype(int),
            },
            {"gamma": np.random.random((1, 2, 3)).astype(bool)},
        ]
        result = QuantumProgramResult(data=data)

        assert len(result) == 2
        assert all(isinstance(item, QuantumProgramItemResult) for item in result)
        assert np.all(result[0]["alpha"] == data[0]["alpha"])
        assert np.all(result[0]["beta"] == data[0]["beta"])
        assert np.all(result[1]["gamma"] == data[1]["gamma"])

    def test_metadata(self):
        """Test the metadata field."""
        data = [{"alpha": np.random.random((1, 2, 3)).astype(bool)}]
        metadata = "metadata"
        result = QuantumProgramResult(data=data, metadata=metadata)

        assert result.metadata == metadata

    def test_passthrough_data(self):
        """Test the passthrough data field."""
        data = [{"alpha": np.random.random((1, 2, 3)).astype(bool)}]
        passthrough_data = {"foo": {"bar": np.random.random((1, 2, 3))}}
        result = QuantumProgramResult(data=data, passthrough_data=passthrough_data)

        assert result.passthrough_data == passthrough_data


class TestQuantumProgramItemResult:
    """Tests the ``QuantumProgramItemResult`` class."""

    def test_result(self):
        """Test initializing a ``QuantumProgramItemResult`` object."""
        result = {
            "alpha": np.random.random((1, 2, 3)).astype(bool),
            "beta": np.random.random((1, 2, 3)).astype(int),
        }
        item = QuantumProgramItemResult(result)

        assert len(item) == 2
        assert np.all(item["alpha"] == result["alpha"])
        assert np.all(item["beta"] == result["beta"])

    def test_metadata(self):
        """Test initializing a ``QuantumProgramItemResult`` object."""
        result = {"alpha": np.random.random((1, 2, 3)).astype(bool)}
        metadata = "metadata"
        item = QuantumProgramItemResult(result, metadata=metadata)

        assert item.metadata == metadata
