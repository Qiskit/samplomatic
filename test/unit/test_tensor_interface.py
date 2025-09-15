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
from qiskit.quantum_info import QubitSparsePauliList

from samplomatic.tensor_interface import (
    Specification,
    TensorInterface,
    TensorSpecification,
    ValueType,
)


class TestSpecification:
    """Test Specification class."""

    def test_specification_describe_and_repr(
        self,
    ):
        spec = Specification("count", ValueType.INT, "an integer count")
        assert "count" in spec.describe() and "int" in spec.describe()
        assert "Optional" not in spec.describe()
        assert repr(spec).startswith("Specification(")

        spec = Specification("count", ValueType.INT, "an integer count", True)
        assert "Optional" in spec.describe()

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

    def test_validate_and_coerce_paulis(self):
        """Test with paulis type."""
        spec = Specification("map", ValueType.PAULIS)
        obj = QubitSparsePauliList.from_list(["XX"])
        assert spec.validate_and_coerce(obj) is obj
        with pytest.raises(TypeError):
            spec.validate_and_coerce("not-paulis")

    def test_validate_and_coerce_numpy_array(self):
        """Test with numpy type."""
        spec = Specification("arr", ValueType.NUMPY_ARRAY)
        out = spec.validate_and_coerce([1, 2, 3])
        assert isinstance(out, np.ndarray)
        np.testing.assert_array_equal(out, np.array([1, 2, 3]))


class TestTensorSpecification:
    """Test the TensorSpecification class."""

    def test_tensor_specification_basic(self):
        """Test basic attributes and methods."""
        ts = TensorSpecification("x", (3,), np.dtype(np.int64), "a vector")
        desc = ts.describe()
        assert "int64" in desc and "[3]" in desc
        assert repr(ts).startswith("TensorSpecification(")
        assert ts.shape == (3,)
        assert ts.ndim == 1
        assert not ts.optional
        assert "Optional" not in desc

        ts = TensorSpecification("x", (3,), np.dtype(np.int64), "a vector", optional=True)
        assert ts.optional
        assert "Optional" in ts.describe()

    def test_tensor_specification_empty_matches_shape_and_dtype(self):
        """Test the empty method gives valid type."""
        ts = TensorSpecification("x", (2, 3), np.dtype(np.float64))
        arr = ts.empty()
        assert arr.shape == (2, 3)
        assert arr.dtype == np.dtype(np.float64)
        ts.validate_and_coerce(arr)

    def test_tensor_specification_validate_and_coerce(self):
        """Test that validate_and_coerce accepts valid input."""
        ts = TensorSpecification("x", (2, 2), np.int64)
        arr = np.zeros((2, 2), dtype=np.int64)
        result = ts.validate_and_coerce(arr)
        assert np.allclose(result, arr)

    def test_tensor_specification_bad_validate_and_coerce(self):
        """Test that validate_and_coerce fails when expected."""
        ts = TensorSpecification("x", (2, 2), np.dtype(np.int64))

        with pytest.raises(ValueError, match="expects an array of dtype int64"):
            ts.validate_and_coerce(np.zeros((2, 2), dtype=np.float32))

        with pytest.raises(ValueError, match="expects an array of shape \\(2, 2\\)"):
            ts.validate_and_coerce(np.zeros((3, 3), dtype=np.int64))

    def test_tensor_specification_validate_and_coerce_broadcast(self):
        """Test that validate_and_coerce accepts valid input when broadcastable."""
        ts = TensorSpecification("x", (2, 2), np.int64, broadcastable=True)
        arr = np.zeros((7, 2, 2), dtype=np.int64)
        result = ts.validate_and_coerce(arr)
        assert np.allclose(result, arr)

    def test_tensor_specification_bad_validate_and_coerce_broadcast(self):
        """Test that validate_and_coerce fails when expected when broadcastable."""
        ts = TensorSpecification("x", (2, 2), np.dtype(np.int64))

        with pytest.raises(ValueError, match="expects an array of dtype int64"):
            ts.validate_and_coerce(np.zeros((7, 2, 2), dtype=np.float32))

        with pytest.raises(ValueError, match="expects an array of shape \\(2, 2\\)"):
            ts.validate_and_coerce(np.zeros((17, 2, 3), dtype=np.int64))


class TestTensorInterface:
    """Test the TensorInterface class."""

    def test_basic_attributes(self):
        """Test basic attributes post-construction."""
        spec1 = Specification("flag", ValueType.BOOL, "boolean flag " * 30)
        spec2 = TensorSpecification("vec", (2,), np.dtype(np.float64), "vector input")
        tensor_interface = TensorInterface([spec2, spec1])

        assert "TensorInterface" in repr(tensor_interface)
        assert "flag' <bool" in tensor_interface.describe()
        assert "*abc123*" in tensor_interface.describe(prefix="*abc123*")
        assert all(len(line) <= 100 for line in tensor_interface.describe(width=100).split("\n"))
        assert [spec.name for spec in tensor_interface.specs] == ["flag", "vec"]
        assert tensor_interface.shape == ()
        assert tensor_interface.size == 1
        assert tensor_interface.ndim == 0

    def test_dunders(self):
        """Test some dunders: contains, delete, len."""
        spec1 = Specification("flag", ValueType.BOOL, "boolean flag")
        spec2 = TensorSpecification("vec", (2,), np.float64, "vector input")
        tensor_interface = TensorInterface([spec1, spec2])

        assert len(tensor_interface) == 0
        assert "flag" not in tensor_interface
        tensor_interface["flag"] = 1
        assert len(tensor_interface) == 1
        assert "flag" in tensor_interface
        assert list(iter(tensor_interface)) == ["flag"]

        tensor_interface["flag"] = 1
        assert tensor_interface["flag"] is True
        del tensor_interface["flag"]
        assert "flag" not in tensor_interface

    def test_invalid_key_assignment_raises(self):
        """Test setting a non-existent key raises ValueError."""
        spec1 = Specification("flag", ValueType.BOOL, "boolean flag")
        spec2 = TensorSpecification("vec", (2,), np.float64, "vector input")
        tensor_interface = TensorInterface([spec1, spec2])

        with pytest.raises(ValueError, match="no specification named 'unknown'"):
            tensor_interface["unknown"] = 123

    def test_fully_bound(self):
        """Test fully_bound property."""
        spec1 = Specification("flag", ValueType.BOOL, "boolean flag")
        spec2 = TensorSpecification("vec", (2,), np.float64, "vector input")
        spec3 = Specification("optional", ValueType.INT, "optional int", True)

        tensor_interface = TensorInterface([spec1, spec2, spec3])
        assert not tensor_interface.fully_bound

        tensor_interface.bind(flag=0)
        assert not tensor_interface.fully_bound

        tensor_interface.bind(vec=np.array([1.0, 2.0]))
        assert tensor_interface.fully_bound

        tensor_interface.bind(optional=1.0)
        assert tensor_interface.fully_bound

    def test_make_broadcastable_returns_new_interface(self):
        """Test make_broadcastable() returns new interface with updated specs."""
        spec = TensorSpecification("arr", (2,), np.float64, broadcastable=False)
        tensor_interface = TensorInterface([spec])
        tensor_interface["arr"] = np.array([1.0, 2.0])
        new_tensor_interface = tensor_interface.make_broadcastable()
        assert new_tensor_interface.specs[0].broadcastable is True
        assert np.allclose(new_tensor_interface["arr"], tensor_interface["arr"])

    def test_broadcast_shape_updates_and_incompatible_shapes_raise(self):
        """Test Broadcast shape updates correctly and incompatible shapes raise ValueError."""
        spec1 = TensorSpecification("x", (2,), np.float64, broadcastable=True)
        spec2 = TensorSpecification("y", (3, 4), np.float64, broadcastable=True)

        tensor_interface = TensorInterface([spec1, spec2])
        assert tensor_interface.shape == ()

        tensor_interface["x"] = np.ones((3, 2), dtype=np.float64)
        assert tensor_interface.shape == (3,)

        with pytest.raises(ValueError, match="because it is not broadcastable"):
            tensor_interface["x"] = np.ones((4, 2), dtype=np.float64)

        with pytest.raises(ValueError, match="because it is not broadcastable"):
            tensor_interface["y"] = np.ones((17, 3, 4), dtype=np.float64)

        tensor_interface["y"] = np.ones((3, 4), dtype=np.float64)
        assert tensor_interface.shape == (3,)

        tensor_interface["y"] = np.ones((17, 3, 3, 4), dtype=np.float64)
        assert tensor_interface.shape == (17, 3)

    def test_getitem_with_slice_returns_new_interface(self):
        """Test indexing with slices returns a new TensorInterface."""
        spec1 = TensorSpecification("x", (2,), np.float64, broadcastable=True)
        spec2 = TensorSpecification("y", (5, 2), np.float64, broadcastable=True)
        spec3 = Specification("z", ValueType.INT, optional=True)
        tensor_interface = TensorInterface([spec1, spec2, spec3])
        tensor_interface["x"] = data_x = np.arange(12, dtype=np.float64).reshape(6, 2)
        tensor_interface["y"] = data_y = np.arange(10, dtype=np.float64).reshape(5, 2)
        tensor_interface["z"] = data_z = 1
        new_tensor_interface = tensor_interface[:3]

        assert isinstance(new_tensor_interface, TensorInterface)
        assert new_tensor_interface is not tensor_interface
        assert np.allclose(new_tensor_interface["x"], data_x[:3])
        assert np.allclose(new_tensor_interface["y"], data_y)
        assert new_tensor_interface["z"] == data_z
        assert new_tensor_interface.specs[2].optional
        assert new_tensor_interface.shape == (3,)

    def test_nested_dict_assignment(self):
        """Test nested dict assignment resolves flattened names correctly."""
        spec1 = Specification("foo.bar", ValueType.INT)
        tensor_interface = TensorInterface([spec1])
        tensor_interface["foo"] = {"bar": 5}
        assert "foo.bar" in tensor_interface
        assert tensor_interface["foo.bar"] == 5
