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

import pytest

from samplomatic.annotations import DecompositionMode
from samplomatic.exceptions import SynthError
from samplomatic.synths import RzRxSynth, RzSxSynth, get_synth


def test_error():
    """Test that it raises an error when the decomposition mode is not supported."""
    with pytest.raises(SynthError, match="Could not get a synth"):
        get_synth("not a mode")


def test_rzrx():
    """Test getting RZRX mode."""
    assert isinstance(get_synth(DecompositionMode.RZRX), RzRxSynth)


def test_rzsx():
    """Test getting RZSX mode."""
    assert isinstance(get_synth(DecompositionMode.RZSX), RzSxSynth)
