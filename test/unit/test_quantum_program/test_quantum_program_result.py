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

from datetime import datetime, timedelta

import numpy as np
import pytest

from samplomatic.quantum_program import (
    ChunkPart,
    ChunkSpan,
    ChunkTiming,
    QuantumProgramItemResult,
    QuantumProgramResult,
)


def _make_chunk_timings(n: int = 5) -> ChunkTiming:
    """Create a synthetic ChunkTiming with ``n`` chunks."""
    t = datetime(year=2025, month=1, day=1)
    spans = []
    for i in range(n):
        start = t + timedelta(seconds=i * 10)
        stop = start + timedelta(seconds=5 + i)
        parts = [ChunkPart(idx_item=i % 2, size=10 + i)]
        spans.append(ChunkSpan(start=start, stop=stop, parts=parts))
    return ChunkTiming(spans)


class TestDrawChunkTiming:
    """Tests for ``ChunkTiming``."""

    def test_len(self):
        """Assert ChunkTiming reports the number of spans it contains."""
        assert len(_make_chunk_timings()) == 5

    def test_getitem_int(self):
        """Assert integer indexing returns a ChunkSpan."""
        item = _make_chunk_timings()[0]
        assert isinstance(item, ChunkSpan)

    def test_getitem_slice(self):
        """Assert slice indexing returns a new ChunkTiming with the selected spans."""
        sliced = _make_chunk_timings()[1:3]
        assert isinstance(sliced, ChunkTiming)
        assert len(sliced) == 2

    def test_iter(self):
        """Assert iteration yields all ChunkSpan objects."""
        items = list(_make_chunk_timings())
        assert len(items) == 5
        assert all(isinstance(s, ChunkSpan) for s in items)

    def test_eq(self):
        """Assert two ChunkTiming built from the same spans compare equal."""
        other = _make_chunk_timings()
        assert _make_chunk_timings() == other

    def test_repr(self):
        """Assert repr includes the class name."""
        assert "ChunkTiming" in repr(_make_chunk_timings())

    def test_start_stop_duration(self):
        """Assert start and stop are datetimes and duration is positive."""
        assert isinstance(_make_chunk_timings().start, datetime)
        assert isinstance(_make_chunk_timings().stop, datetime)
        assert _make_chunk_timings().duration > 0

    def test_draw(self):
        """Test the draw method."""
        timings = _make_chunk_timings()
        timings.draw()


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

    def test_timing(self):
        """Test the ``timing`` property."""
        data = [{"alpha": np.random.random((1, 2, 3)).astype(bool)}]
        result = QuantumProgramResult(data=data)

        with pytest.raises(NotImplementedError):
            result.timing

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
