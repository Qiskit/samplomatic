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

from samplomatic.tensor_interface import (
    PauliLindbladMapSpecification,
    TensorInterface,
    TensorSpecification,
)


class TestTensorSpecification:
    def test_simple_construction_and_attributes(self):
        spec = TensorSpecification(
            name="input_tensor",
            shape=("batch", 3, 224, 224),
            dtype=np.float32,
            description="An input tensor",
            broadcastable=True,
            optional=True,
        )

        assert spec.name == "input_tensor"
        assert spec.description == "An input tensor"
        assert spec.optional is True
        assert spec.broadcastable is True
        assert spec.dtype == np.float32
        assert spec.shape == ("batch", 3, 224, 224)
        assert spec.free_dimensions == {"batch"}
        assert spec.ndim == 4

    def test_describe(self):
        spec = TensorSpecification(
            name="features",
            shape=("batch", 128),
            dtype=np.float64,
            description="My vector",
            broadcastable=False,
            optional=False,
        )

        expected = "'features' <float64['batch', 128]>: My vector"
        assert spec.describe() == expected

    def test_repr(self):
        spec = TensorSpecification(
            name="input",
            shape=("batch", 64),
            dtype=np.int32,
            description="Input tensor",
            broadcastable=True,
            optional=True,
        )

        assert repr(spec) == (
            "TensorSpecification('input', ('batch', 64), dtype('int32'), "
            "'Input tensor', broadcastable=True, optional=True)"
        )

        spec_minimal = TensorSpecification(
            name="input",
            shape=(32,),
            dtype=np.float32,
        )

        assert repr(spec_minimal) == "TensorSpecification('input', (32,), dtype('float32'))"

    def test_validate_and_coerce_success(self):
        spec = TensorSpecification(
            name="features",
            shape=("batch", 128),
            dtype=np.float32,
            broadcastable=False,
            optional=False,
        )

        input_array = np.ones((4, 128), dtype=np.float64)  # dtype will be coerced
        coerced, bound_dims = spec.validate_and_coerce(input_array)

        assert isinstance(coerced, np.ndarray)
        assert coerced.shape == (4, 128)
        assert coerced.dtype == np.float32
        assert bound_dims == {"batch": 4}

    def test_validate_and_coerce_broadcastable_success(self):
        spec = TensorSpecification(
            name="features",
            shape=("batch", 128),
            dtype=np.float32,
            description="Feature vector",
            broadcastable=True,
            optional=False,
        )

        input_array = np.ones((2, 4, 128), dtype=np.float64).tolist()  # dtype will be coerced

        coerced, bound_dims = spec.validate_and_coerce(input_array)

        assert isinstance(coerced, np.ndarray)
        assert coerced.shape == (2, 4, 128)
        assert coerced.dtype == np.float32
        assert bound_dims == {"batch": 4}

    def test_validate_and_coerce_not_array(self):
        spec = TensorSpecification("x", (2,), np.float32)
        arr = [[1, 2], [1]]  # ragged
        with pytest.raises(ValueError, match=r"expects an array but received"):
            spec.validate_and_coerce(arr)

    def test_validate_and_coerce_not_castable(self):
        spec = TensorSpecification("x", (2,), np.uint32)
        # complex dtype can't be safely cast to int32
        arr = np.array([{1.2}, {2.3}])
        with pytest.raises(ValueError, match=r"expected to be castable to type"):
            spec.validate_and_coerce(arr)

    def test_validate_and_coerce_too_few_dimensions(self):
        spec = TensorSpecification("x", (2, 3), np.float32)
        arr = np.ones((3,), dtype=np.float32)
        with pytest.raises(ValueError, match=r"must have at least 2 axes"):
            spec.validate_and_coerce(arr)

    def test_validate_and_coerce_inconsistent_free_dimensions(self):
        spec = TensorSpecification("x", ("d", "d"), np.float32)
        arr = np.ones((2, 3), dtype=np.float32)
        with pytest.raises(ValueError, match=r"self-inconsistent values for the free dimension"):
            spec.validate_and_coerce(arr)

    def test_validate_and_coerce_broadcastable_shape_mismatch(self):
        spec = TensorSpecification("x", (2, 3), np.float32, broadcastable=True)
        arr = np.ones((4, 2, 4), dtype=np.float32)
        with pytest.raises(ValueError, match=r"expects an array ending with shape"):
            spec.validate_and_coerce(arr)

    def test_validate_and_coerce_strict_shape_mismatch(self):
        spec = TensorSpecification("x", (2, 3), np.float32, broadcastable=False)
        arr = np.ones((2, 4), dtype=np.float32)
        with pytest.raises(ValueError, match=r"expects an array of shape"):
            spec.validate_and_coerce(arr)


class TestPauliLindbladMapSpecification:
    def test_simple_construction_and_attributes(self):
        spec = PauliLindbladMapSpecification("noise", num_qubits=3, num_terms="n_terms")

        assert spec.name == "noise"
        assert spec.num_qubits == 3
        assert spec.num_terms == "n_terms"
        assert spec.optional is False
        assert spec.free_dimensions == {"n_terms"}
        assert spec.description == "A PauliLindblad map acting on 3 qubits, with 'n_terms' terms."

    def test_describe(self):
        spec = PauliLindbladMapSpecification("noise", num_qubits=3, num_terms="n_terms")
        assert (
            spec.describe() == "'noise' <PauliLindbladMap>: A PauliLindblad map acting "
            "on 3 qubits, with 'n_terms' terms."
        )

    def test_repr(self):
        spec = PauliLindbladMapSpecification("noise", num_qubits=3, num_terms="n_terms")
        expected = "PauliLindbladMapSpecification('noise', num_qubits=3, num_terms=n_terms)"
        assert repr(spec) == expected

    def test_validate_and_coerce_success(self):
        spec = PauliLindbladMapSpecification("noise", num_qubits=3, num_terms="n_terms")
        lindblad = PauliLindbladMap.from_list([("IXI", 0.3)])

        coerced, bound_dims = spec.validate_and_coerce(lindblad)

        assert coerced is lindblad
        assert bound_dims == {"n_terms": 1}

    def test_validate_and_coerce_wrong_type(self):
        spec = PauliLindbladMapSpecification("noise", num_qubits=3, num_terms="n_terms")
        with pytest.raises(ValueError, match=r"Expected a PauliLindbladMap, but received"):
            spec.validate_and_coerce("not a lindblad map")

    def test_validate_and_coerce_wrong_num_qubits(self):
        spec = PauliLindbladMapSpecification("noise", num_qubits=3, num_terms="n_terms")
        lindblad = PauliLindbladMap.from_list([("IZ", 0.5)])
        with pytest.raises(ValueError, match=r"Expected a PauliLindbladMap acting on 3"):
            spec.validate_and_coerce(lindblad)


class TestTensorInterface:
    def test_simple_construction_and_attributes(self):
        specs = [
            TensorSpecification("a", (2, 3), np.float32),
            TensorSpecification("b", ("n",), np.int64, optional=True),
        ]
        interface = TensorInterface(specs)

        assert interface.specs == sorted(specs, key=lambda s: s.name)
        assert interface.free_dimensions == {"n"}
        assert not interface.fully_bound
        assert interface.shape == ()
        assert interface.ndim == 0
        assert interface.size == 1

    def test_free_dimension(self):
        interface = TensorInterface(
            [
                TensorSpecification("x", ("n",), np.float32),
                TensorSpecification("y", ("n",), np.float32),
            ]
        )
        assert interface.bound_dimensions == {}
        interface["x"] = np.ones((5,), dtype=np.float32)
        assert interface.bound_dimensions == {"n": 5}

    def test_make_broadcastable(self):
        specs = [
            TensorSpecification("a", (2, 3), np.float32, broadcastable=False),
            TensorSpecification("b", ("n",), np.int64, broadcastable=False),
        ]
        interface = TensorInterface(specs)

        interface["a"] = np.ones((2, 3), dtype=np.float32)
        interface["b"] = np.arange(5, dtype=np.int64)

        broadcastable_interface = interface.make_broadcastable()

        # check that all specs are now broadcastable
        for spec in broadcastable_interface.specs:
            if isinstance(spec, TensorSpecification):
                assert spec.broadcastable is True

        # check that data was preserved
        assert broadcastable_interface["a"].shape == (2, 3)
        assert np.array_equal(broadcastable_interface["b"], np.arange(5, dtype=np.int64))

        # bind a bigger shape
        broadcastable_interface["b"] = np.arange(50, dtype=np.int64).reshape(2, 5, 5)
        assert broadcastable_interface.shape == (2, 5)

    def test_mapping_interface(self):
        specs = [
            TensorSpecification("x", (4,), np.float32),
            TensorSpecification("y", (4,), np.float32),
        ]
        interface = TensorInterface(specs)

        # initially empty
        assert "x" not in interface
        assert "y" not in interface
        assert len(interface) == 0

        # set items
        interface["x"] = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32)
        interface["y"] = np.array([5.0, 6.0, 7.0, 8.0], dtype=np.float32)

        # get items
        assert np.array_equal(interface["x"], np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32))
        assert np.array_equal(interface["y"], np.array([5.0, 6.0, 7.0, 8.0], dtype=np.float32))

        # membership and length
        assert "x" in interface
        assert "y" in interface
        assert len(interface) == 2

        # iteration
        keys = set(iter(interface))
        assert keys == {"x", "y"}

        # deletion
        del interface["x"]
        assert "x" not in interface
        assert len(interface) == 1

    def test_getitem_slicing_mode(self):
        specs = [
            TensorSpecification("a", (2,), np.float32, broadcastable=True),
            TensorSpecification("b", (2,), np.float32, broadcastable=False),
        ]
        interface = TensorInterface(specs)

        # note first item gives shape (3, 4)
        interface["a"] = np.arange(24).reshape((3, 4, 2))
        interface["b"] = np.array([10.0, 20.0], dtype=np.float32)

        sliced = interface[0]
        assert sliced is not interface
        assert isinstance(sliced, TensorInterface)
        assert sliced.shape == (4,)

        assert np.array_equal(sliced["a"], interface["a"][0])
        assert np.array_equal(sliced["b"], interface["b"])
        assert [spec.name for spec in sliced.specs] == ["a", "b"]

    def test_setitem_invalid_key(self):
        interface = TensorInterface([TensorSpecification("x", (2,), np.float32)])
        with pytest.raises(ValueError, match=r"The interface has no specification named 'y'"):
            interface["y"] = np.array([1.0, 2.0], dtype=np.float32)

    def test_setitem_inconsistent_free_dimension(self):
        interface = TensorInterface(
            [
                TensorSpecification("x", ("n",), np.float32),
                TensorSpecification("y", ("n",), np.float32),
            ]
        )
        interface["x"] = np.ones((5,), dtype=np.float32)
        with pytest.raises(ValueError, match=r"Inconsistent values for the free dimension 'n'"):
            interface["y"] = np.ones((6,), dtype=np.float32)

    def test_setitem_broadcast_shape_mismatch(self):
        interface = TensorInterface(
            [
                TensorSpecification("x", (2,), np.float32, broadcastable=True),
                TensorSpecification("y", (2,), np.float32, broadcastable=True),
            ]
        )
        interface["x"] = np.ones((3, 2), dtype=np.float32)
        with pytest.raises(ValueError, match=r"not broadcastable with the current interface shape"):
            interface["y"] = np.ones((4, 2), dtype=np.float32)

    def test_str_and_repr_do_not_fail(self):
        specs = [
            TensorSpecification("x", (2,), np.float32),
            TensorSpecification("y", (3,), np.int64, optional=True),
            PauliLindbladMapSpecification("noise", 2, "num_terms"),
        ]
        interface = TensorInterface(specs)
        interface["x"] = np.array([1.0, 2.0], dtype=np.float32)

        assert isinstance(str(interface), str)
        assert isinstance(repr(interface), str)

    def test_describe_contains_expected_fragments(self):
        specs = [
            TensorSpecification("x", ("n",), np.float32, description="Input vector"),
            TensorSpecification("y", (3,), np.int64, optional=True, description="Class labels"),
        ]
        interface = TensorInterface(specs)
        interface["x"] = np.ones((5,), dtype=np.float32)

        # basic description
        desc = interface.describe()
        assert "'x' <float32['n']>: Input vector" in desc
        assert "'y' <int64[3]>: (Optional) Class labels" in desc

        # include free dimensions
        desc_with_dims = interface.describe(include_free_dimensions=True)
        assert "Dimension constraints: n=5" in desc_with_dims

        # custom prefix
        desc_custom_prefix = interface.describe(prefix="- ", bound_prefix="* ")
        assert "* 'x' <float32['n']>: Input vector" in desc_custom_prefix
        assert "- 'y' <int64[3]>: (Optional) Class labels" in desc_custom_prefix

        # wrapping
        desc_wrapped = interface.describe(width=60)
        assert all(len(line) <= 60 for line in desc_wrapped.splitlines())
