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

"""Unit tests for TraceInfo."""

import pytest

from samplomatic.trace_info import TraceInfo


def test_from_emission_trace_refs_non_empty():
    """Non-empty refs produce singleton sets; empty/missing refs are dropped."""
    result = TraceInfo.from_emission_trace_refs({"tag": "t0", "inject_noise": "", "other": "x"})
    assert result is not None
    assert result.trace_refs == {"tag": {"t0"}, "other": {"x"}}


@pytest.mark.parametrize("refs", [{}, {"tag": "", "inject_noise": ""}])
def test_from_emission_trace_refs_empty_returns_none(refs):
    """All-empty or empty dict returns None."""
    assert TraceInfo.from_emission_trace_refs(refs) is None


def test_merge():
    """Merge performs set union on overlapping keys and copies disjoint keys."""
    a = TraceInfo({"tag": {"t0", "t1"}, "noise": {"n0"}})
    b = TraceInfo({"tag": {"t1", "t2"}, "other": {"x"}})
    a.merge(b)
    assert a.trace_refs == {"tag": {"t0", "t1", "t2"}, "noise": {"n0"}, "other": {"x"}}


def test_style_data():
    """style_data returns a dict with sorted value lists."""
    ti = TraceInfo({"tag": {"b", "a"}, "noise": {"n0"}})
    result = ti.style_data()
    assert result == {"tag": ["a", "b"], "noise": ["n0"]}
    assert TraceInfo(trace_refs={}).style_data() == {}
