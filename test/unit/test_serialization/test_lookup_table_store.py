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
import pytest

from samplomatic.serialization.lookup_table_store import (
    LookupTableStore,
    active_lookup_table_store,
    get_lookup_table_store,
)


def test_register_returns_key():
    store = LookupTableStore()
    arr = np.array([1, 2, 3], dtype=np.int64)
    key = store.register("N1", "foo", arr)
    assert key == "N1:foo"


def test_lookup_success():
    store = LookupTableStore()
    arr = np.array([10, 20], dtype=np.int64)
    store.register("N2", "bar", arr)
    result = store.lookup("N2:bar")
    np.testing.assert_array_equal(result, arr)


def test_lookup_missing_raises():
    store = LookupTableStore()
    with pytest.raises(KeyError):
        store.lookup("N99:missing")


def test_last_write_wins():
    store = LookupTableStore()
    arr1 = np.array([1, 2], dtype=np.int64)
    arr2 = np.array([3, 4], dtype=np.int64)
    store.register("N3", "tbl", arr1)
    store.register("N3", "tbl", arr2)
    np.testing.assert_array_equal(store.lookup("N3:tbl"), arr2)


def test_idempotent_registration_same_content():
    store = LookupTableStore()
    arr = np.array([5, 6, 7], dtype=np.int64)
    key1 = store.register("N4", "t", arr)
    key2 = store.register("N4", "t", arr)
    assert key1 == key2
    np.testing.assert_array_equal(store.lookup(key1), arr)


def test_bool_empty():
    store = LookupTableStore()
    assert not store


def test_bool_nonempty():
    store = LookupTableStore()
    store.register("N5", "x", np.array([1], dtype=np.int64))
    assert store


@pytest.mark.parametrize(
    "arr",
    [
        np.array([[1, 2], [3, 4]], dtype=np.int64),
        np.array([1.0 + 2j, 3.0 - 4j], dtype=np.complex128),
        np.array([0, 1, 255], dtype=np.uint8),
        np.array([[0, 1], [2, 3]], dtype=np.intp),
    ],
)
def test_json_round_trip(arr):
    store = LookupTableStore()
    store.register("N6", "arr", arr)
    json_str = store.to_json()
    restored = LookupTableStore.from_json(json_str)
    result = restored.lookup("N6:arr")
    np.testing.assert_array_equal(result, arr)
    assert result.shape == arr.shape


def test_json_round_trip_intp_dtype_preserved():
    arr = np.array([0, 1, 2], dtype=np.intp)
    store = LookupTableStore()
    store.register("N7", "idx", arr)
    restored = LookupTableStore.from_json(store.to_json())
    assert restored.lookup("N7:idx").dtype == np.dtype(np.intp)


def test_json_round_trip_empty():
    store = LookupTableStore()
    restored = LookupTableStore.from_json(store.to_json())
    assert not restored


def test_context_var_accessor_none_by_default():
    assert get_lookup_table_store() is None


def test_context_var_accessor_returns_store():
    store = LookupTableStore()
    with active_lookup_table_store(store):
        assert get_lookup_table_store() is store


def test_context_var_reset_after_use():
    store = LookupTableStore()
    with active_lookup_table_store(store):
        pass
    assert get_lookup_table_store() is None
