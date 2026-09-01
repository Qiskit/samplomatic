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

import datetime

import pytest

from samplomatic.quantum_program import ChunkPart, ChunkSpan, ChunkTiming


def _make_span(start_s: float, stop_s: float, size: int = 1) -> ChunkSpan:
    """Build a ``ChunkSpan`` with a single ``ChunkPart``."""
    epoch = datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc)
    return ChunkSpan(
        start=epoch + datetime.timedelta(seconds=start_s),
        stop=epoch + datetime.timedelta(seconds=stop_s),
        parts=[ChunkPart(idx_item=0, size=size)],
    )


class TestChunkTiming:
    """Tests the ``ChunkTiming`` class."""

    def test_len_and_iter(self):
        """Supports len() and iteration over the wrapped spans."""
        spans = [_make_span(0, 1), _make_span(1, 2), _make_span(2, 3)]
        timing = ChunkTiming(spans)
        assert len(timing) == 3
        assert list(timing) == spans

    def test_getitem_int(self):
        """Integer indexing returns the corresponding ChunkSpan."""
        spans = [_make_span(0, 1), _make_span(1, 2)]
        timing = ChunkTiming(spans)
        assert timing[0] == spans[0]
        assert timing[1] == spans[1]

    def test_getitem_slice(self):
        """Slice indexing returns a new ChunkTiming."""
        spans = [_make_span(i, i + 1) for i in range(4)]
        sliced = ChunkTiming(spans)[1:3]
        assert isinstance(sliced, ChunkTiming)
        assert list(sliced) == spans[1:3]

    def test_start_stop_duration(self):
        """start, stop, and duration are derived from the spans."""
        spans = [_make_span(10, 20, size=3), _make_span(25, 40, size=7)]
        timing = ChunkTiming(spans)
        epoch = datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc)
        assert timing.start, epoch + datetime.timedelta(seconds=10)
        assert timing.stop, epoch + datetime.timedelta(seconds=40)
        assert timing.duration, pytest.approx(30.0)
