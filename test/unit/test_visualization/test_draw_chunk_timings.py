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

"""Unit tests for draw_chunk_timings."""

from datetime import datetime, timedelta

import pytest

from samplomatic.quantum_program import (
    ChunkPart,
    ChunkSpan,
    ChunkTiming,
    Metadata,
    QuantumProgramResult,
)
from samplomatic.visualization.draw_chunk_timings import draw_chunk_timings


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
    """Tests for ``draw_chunk_timings``."""

    @pytest.mark.parametrize("normalize_y", [True, False])
    def test_draw_normalize_y(self, normalize_y):
        """Verify draw_chunk_timings renders without error with normalize_y on and off."""
        draw_chunk_timings(_make_chunk_timings(), normalize_y=normalize_y)

    def test_draw_common_start(self):
        """Verify draw_chunk_timings renders without error when common_start=True."""
        draw_chunk_timings(_make_chunk_timings(), common_start=True)

    def test_draw_with_name(self):
        """Verify draw_chunk_timings renders without error when a name is provided."""
        draw_chunk_timings(_make_chunk_timings(), names="my_job")

    def test_draw_empty(self):
        """Verify draw_chunk_timings handles an empty ChunkTiming without error."""
        draw_chunk_timings(ChunkTiming([]))

    @pytest.mark.parametrize(
        ["normalize_y", "common_start", "width", "names"],
        [
            (False, False, 4, None),
            (True, True, 8, "alpha"),
            (True, False, 4, ["alpha", "beta"]),
        ],
    )
    def test_two_chunk_timings(self, normalize_y, common_start, width, names):
        """Verify draw_chunk_timings renders two ChunkTiming for cross-job comparison."""
        ct2 = _make_chunk_timings(n=3)
        draw_chunk_timings(
            _make_chunk_timings(),
            ct2,
            normalize_y=normalize_y,
            common_start=common_start,
            line_width=width,
            names=names,
        )

    def test_draw_method(self):
        """Verify ChunkTiming.draw() renders without error."""
        _make_chunk_timings().draw()

    def test_draw_method_normalize_y(self):
        """Verify ChunkTiming.draw() renders without error when normalize_y=True."""
        _make_chunk_timings().draw(normalize_y=True)

    def test_result_chunk_timings_property(self):
        """Assert QuantumProgramResult.chunk_timings wraps the metadata spans."""
        metadata = Metadata(chunk_timing=list(_make_chunk_timings()))
        result = QuantumProgramResult(data=[], metadata=metadata)
        assert isinstance(result.timing, ChunkTiming)
        assert len(result.timing) == len(_make_chunk_timings())

    def test_result_chunk_timings_empty(self):
        """Assert QuantumProgramResult.chunk_timings is empty when no metadata spans are present."""
        result = QuantumProgramResult(data=[])
        assert isinstance(result.timing, ChunkTiming)
        assert len(result.timing) == 0
