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

from samplomatic.optionals import HAS_PLOTLY
from samplomatic.quantum_program import (
    ChunkPart,
    ChunkSpan,
    ChunkTiming,
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


@pytest.mark.skipif(not HAS_PLOTLY, reason="plotly is not installed")
class TestDrawChunkTiming:
    """Tests for ``draw_chunk_timings``."""

    @pytest.mark.parametrize("normalize_y", [True, False])
    def test_draw_normalize_y(self, normalize_y, save_plot):
        """Verify draw_chunk_timings renders without error with normalize_y on and off."""
        plot = draw_chunk_timings(_make_chunk_timings(), normalize_y=normalize_y)
        save_plot(plot)

    def test_draw_common_start(self, save_plot):
        """Verify draw_chunk_timings renders without error when common_start=True."""
        plot = draw_chunk_timings(_make_chunk_timings(), common_start=True)
        save_plot(plot)

    def test_draw_with_name(self, save_plot):
        """Verify draw_chunk_timings renders without error when a name is provided."""
        plot = draw_chunk_timings(_make_chunk_timings(), names="my_job")
        save_plot(plot)

    def test_draw_empty(self, save_plot):
        """Verify draw_chunk_timings handles an empty ChunkTiming without error."""
        plot = draw_chunk_timings(ChunkTiming([]))
        save_plot(plot)

    @pytest.mark.parametrize(
        ["normalize_y", "common_start", "width", "names"],
        [
            (False, False, 4, None),
            (True, True, 8, "alpha"),
            (True, False, 4, ["alpha", "beta"]),
        ],
    )
    def test_two_chunk_timings(self, normalize_y, common_start, width, names, save_plot):
        """Verify draw_chunk_timings renders two ChunkTiming for cross-job comparison."""
        ct2 = _make_chunk_timings(n=3)
        plot = draw_chunk_timings(
            _make_chunk_timings(),
            ct2,
            normalize_y=normalize_y,
            common_start=common_start,
            line_width=width,
            names=names,
        )
        save_plot(plot)

    def test_draw_method(self, save_plot):
        """Verify ChunkTiming.draw() renders without error."""
        plot = _make_chunk_timings().draw()
        save_plot(plot)

    def test_draw_method_normalize_y(self, save_plot):
        """Verify ChunkTiming.draw() renders without error when normalize_y=True."""
        plot = _make_chunk_timings().draw(normalize_y=True)
        save_plot(plot)
