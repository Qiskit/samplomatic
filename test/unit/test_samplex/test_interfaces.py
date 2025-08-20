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
from qiskit.quantum_info import PauliLindbladMap

from samplomatic.exceptions import SamplexInputError
from samplomatic.samplex import SamplexInput, SamplexOutput, Specification, TensorSpecification
from samplomatic.samplex.interfaces import ValueType


class TestSpecification:
    """Test Specification class."""

    def test_specification_describe_and_repr(
        self,
    ):
        spec = Specification("count", ValueType.INT, "an integer count")
        assert "count" in spec.describe() and "int" in spec.describe()
        assert repr(spec).startswith("Specification(")

    @pytest.mark.parametrize("val, expected", [(0, False), (1, True), ("", False)])
    def test_validate_and_coerce_bool(self, val, expected):
        """Test with bool type."""
        spec = Specification("flag", ValueType.BOOL)
        assert spec.validate_and_coerce(val) is expected

    def test_validate_and_coerce_int(self):
        """Test with int type."""
        spec = Specification("num", ValueType.INT)
        assert spec.validate_and_coerce(30) == 30
        assert spec.validate_and_coerce("5") == 5

    def test_validate_and_coerce_lindblad(self):
        """Test with lindblad type."""
        spec = Specification("map", ValueType.LINDBLAD)
        obj = PauliLindbladMap.from_list([("XX", 0.5)])
        assert spec.validate_and_coerce(obj) is obj
        with pytest.raises(TypeError):
            spec.validate_and_coerce("not-lindblad")

    def test_validate_and_coerce_numpy_array(self):
        """Test with numpy type."""
        spec = Specification("arr", ValueType.NUMPY_ARRAY)
        out = spec.validate_and_coerce([1, 2, 3])
        assert isinstance(out, np.ndarray)
        np.testing.assert_array_equal(out, np.array([1, 2, 3]))


class TestTensorSpecification:
    """Test the TensorSpecification class."""

    def test_tensor_specification_describe_and_repr(self):
        ts = TensorSpecification("x", (3,), np.int64, "a vector")
        desc = ts.describe()
        assert "int64" in desc and "[3]" in desc
        assert repr(ts).startswith("TensorSpecification(")

    def test_tensor_specification_empty_matches_shape_and_dtype(self):
        ts = TensorSpecification("x", (2, 3), np.float64)
        arr = ts.empty()
        assert arr.shape == (2, 3)
        assert arr.dtype == np.float64

    def test_tensor_specification_validate_and_coerce_accepts_correct_array(self):
        ts = TensorSpecification("x", (2, 2), np.int64)
        arr = np.zeros((2, 2), dtype=np.int64)
        result = ts.validate_and_coerce(arr)
        assert np.allclose(result, arr)

    def test_tensor_specification_validate_and_coerce_rejects_bad_shape_or_dtype(self):
        ts = TensorSpecification("x", (2, 2), np.int64)
        bad_shape = np.zeros((3, 3), dtype=np.int64)
        bad_dtype = np.zeros((2, 2), dtype=np.float32)
        with pytest.raises(SamplexInputError):
            ts.validate_and_coerce(bad_shape)
        with pytest.raises(SamplexInputError):
            ts.validate_and_coerce(bad_dtype)


class TestSamplexInput:
    """Test ``SamplexInput``."""

    def test_empty(self):
        """Test an empty output."""
        samplex_input = SamplexInput([], {})
        assert len(samplex_input) == 0
        assert not list(samplex_input)
        assert samplex_input.fully_bound

    def test_bind(self):
        """Test the bind method."""

        samplex_input = SamplexInput(
            [
                TensorSpecification("a", (5,), np.uint8, "desc_a"),
                TensorSpecification("b", (3, 7), np.float32, "desc_b"),
                TensorSpecification("c.d", (), np.float64, "desc_c_d"),
                TensorSpecification("e", (), np.float64, "has_a_default"),
            ],
            {"e": np.float64(0.2)},
        )

        assert not samplex_input.fully_bound
        assert len(samplex_input) == 0
        assert list(samplex_input) == []
        assert samplex_input["e"] == np.float64(0.2)

        samplex_input.bind(a=np.arange(5, dtype=np.uint8), b=np.zeros((3, 7), np.float32))

        assert not samplex_input.fully_bound
        assert np.array_equal(samplex_input["a"], np.arange(5, dtype=np.uint8))
        assert np.array_equal(samplex_input["b"], np.zeros((3, 7), np.float32))

        samplex_input.bind(c={"d": np.float64(0.5)})

        assert samplex_input.fully_bound
        assert samplex_input["c.d"] == np.float64(0.5)

    def test_dunders(self):
        """Test the bind method."""

        samplex_input = SamplexInput(
            [
                TensorSpecification("a", (5,), np.uint8, "desc_a"),
                TensorSpecification("b", (3, 7), np.float32, "desc_b"),
                TensorSpecification("c.d", (), np.float64, "desc_c_d"),
                TensorSpecification("e", (), np.float64, "has_a_default"),
            ],
            {"e": (e := np.float64(0.2))},
        )

        assert len(samplex_input) == 0
        assert not list(samplex_input)

        # __setitem__
        samplex_input["b"] = b = np.linspace(0, 1, 21).reshape(3, 7).astype(np.float32)
        samplex_input["c"] = {"d": (cd := 3.1)}

        assert len(samplex_input) == 2
        assert list(samplex_input) == ["b", "c.d"]

        # __contains__
        assert "b" in samplex_input
        assert "c.d" in samplex_input
        assert "e" in samplex_input

        # __getitem__
        assert np.allclose(samplex_input["b"], b)
        assert np.allclose(samplex_input["c.d"], cd)
        assert np.allclose(samplex_input["e"], e)

    def test_describe(self):
        """Test the describe() method."""

        samplex_input = SamplexInput(
            [
                TensorSpecification("a", (5,), np.uint8, "desc_a"),
                TensorSpecification("b", (3, 7), np.float32, "desc_b"),
                TensorSpecification("c.d", (), np.float64, "desc_c_d"),
                TensorSpecification("e", (), np.float64, "has_a_default"),
            ],
            {"e": np.float64(0.2)},
        )

        samplex_input["b"] = np.linspace(0, 1, 21).reshape(3, 7).astype(np.float32)

        assert "desc_a" in samplex_input.describe()
        assert "c.d" in samplex_input.describe()
        assert "desc_c_d" in samplex_input.describe()
        assert "has_a_default" in samplex_input.describe()

        assert samplex_input.describe(prefix="***").count("***") == 4

        assert "desc_b" not in samplex_input.describe(include_bound=False)
        assert "has_a_default" not in samplex_input.describe(include_bound=False)

    def test_exceptions(self):
        """Test exceptions."""

        input = SamplexInput(
            [
                TensorSpecification("a", (5,), np.uint8, "desc_a"),
                TensorSpecification("b", (3, 7), np.float32, "desc_b"),
            ],
            {},
        )
        b = np.zeros((3, 7), np.float32)

        with pytest.raises(ValueError, match="The interface has no specification named 'no_input'"):
            input.bind(no_input=b)

        with pytest.raises(ValueError, match="The interface has no specification named 'no_input'"):
            input["no_input"] = b

        with pytest.raises(SamplexInputError, match="expects an array"):
            input.bind(a=np.zeros((5,), np.float32), b=b)

        with pytest.raises(SamplexInputError, match="expects an array"):
            input.bind(a=np.zeros((7,), np.uint8), b=b)


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
