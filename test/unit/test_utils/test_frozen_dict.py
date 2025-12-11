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

"""Tests for ``FrozenDict``"""

import pytest

from samplomatic.utils import FrozenDict


def test_basic_item_access_and_len():
    """Test access and length."""
    frozen_dict = FrozenDict({"a": 1, "b": 2})
    assert frozen_dict["a"] == 1
    assert len(frozen_dict) == 2
    assert "b" in frozen_dict
    assert "c" not in frozen_dict


def test_constructor():
    """Test that we can do standard dict-like constructions."""
    assert FrozenDict({"a": 1, "b": 2}) == {"a": 1, "b": 2}
    assert FrozenDict(a=1, b=2) == {"a": 1, "b": 2}
    assert FrozenDict([("a", 1), ("b", 2)]) == {"a": 1, "b": 2}


def test_views_are_readonly_and_ordered():
    """Test views are read-only and ordered."""
    frozen_dict = FrozenDict({"x": 1, "y": 2})
    assert list(frozen_dict.keys()) == ["x", "y"]
    assert list(frozen_dict.values()) == [1, 2]
    assert list(frozen_dict.items()) == [("x", 1), ("y", 2)]
    with pytest.raises(AttributeError):
        frozen_dict.items().add(("z", 3))  # mapping views are read-only


def test_get_with_default():
    """Test get returns default."""
    frozen_dict = FrozenDict({"a": 1})
    assert frozen_dict.get("a") == 1
    assert frozen_dict.get("missing") is None
    assert frozen_dict.get("missing", 42) == 42


def test_repr():
    """Test repr looks okay."""
    frozen_dict = FrozenDict({"a": 1, "b": 2})
    r = repr(frozen_dict)
    assert r.startswith("FrozenDict(") and r.endswith(")")
    assert "{'a': 1, 'b': 2}" in r or "{'b': 2, 'a': 1}" in r


def test_immutability_item_and_attr():
    """Test immutability for items and attributes."""
    frozen_dict = FrozenDict({"a": 1})
    with pytest.raises(TypeError, match="FrozenDict is immutable"):
        frozen_dict["a"] = 2
    with pytest.raises(TypeError, match="FrozenDict is immutable"):
        del frozen_dict["a"]
    with pytest.raises(AttributeError, match="FrozenDict is immutable"):
        frozen_dict.new_attr = 123


def test_equality_with_dict_and_mapping():
    """Test equality with dict and mapping."""
    frozen_dict = FrozenDict({"a": 1, "b": 2})
    assert frozen_dict == {"a": 1, "b": 2}
    assert frozen_dict == FrozenDict({"a": 1, "b": 2})
    assert frozen_dict != {"a": 1}

    class WeirdDictType(dict): ...

    assert frozen_dict == WeirdDictType({"a": 1, "b": 2})


def test_hashable_when_contents_hashable():
    """Test hashing succeeds for hashable contents."""
    frozen_dict = FrozenDict({"a": 1, "b": (2, 3)})
    assert frozen_dict in {frozen_dict}
    assert hash(frozen_dict) == hash(frozen_dict)


def test_hash_raises_for_unhashable_contents():
    """Test hashing raises when contents are unhashable."""
    frozen_dict = FrozenDict({"a": []})
    with pytest.raises(TypeError, match="keys and values must all be hashable"):
        hash(frozen_dict)


def test_copy_returns_self():
    """Test copy returns self."""
    frozen_dict = FrozenDict({"a": 1})
    assert frozen_dict.copy() is frozen_dict


def test_merge_or_returns_new_instance_and_other_wins():
    """Test | returns new instance with other taking precedence."""
    frozen_dict = FrozenDict({"a": 1, "b": 2})
    result = frozen_dict | {"b": 99, "c": 3}
    assert isinstance(result, FrozenDict)
    assert result is not frozen_dict
    assert result == {"a": 1, "b": 99, "c": 3}


def test_merge_ror_other_precedence():
    """Test other | frozen_dict gives frozen_dict precedence."""
    frozen_dict = FrozenDict({"a": 1, "b": 2})
    result = {"b": 99, "c": 3} | frozen_dict
    assert isinstance(result, FrozenDict)
    assert result == {"a": 1, "b": 2, "c": 3}


def test_ior_returns_new_instance_and_rebinds():
    """Test |= returns new instance and rebinds variable."""
    frozen_dict = FrozenDict({"x": 1})
    alias = frozen_dict
    frozen_dict |= {"x": 2, "y": 3}
    assert frozen_dict == {"x": 2, "y": 3}
    assert alias == {"x": 1}
    assert frozen_dict is not alias


def test_contains_and_iteration():
    """Test membership and iteration order."""
    frozen_dict = FrozenDict({"k1": 10, "k2": 20})
    assert "k1" in frozen_dict and "k3" not in frozen_dict
    assert list(iter(frozen_dict)) == ["k1", "k2"]
