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

"""get_synth"""

from ..annotations import DecompositionMode
from ..exceptions import SynthError
from .rzrx_synth import RzRxSynth
from .rzsx_synth import RzSxSynth
from .synth import Synth


def get_synth(decomposition_mode: DecompositionMode) -> Synth:
    """Get a synthesizer for the given decomposition mode."""
    if decomposition_mode is DecompositionMode.RZSX:
        return RzSxSynth()
    if decomposition_mode is DecompositionMode.RZRX:
        return RzRxSynth()
    raise SynthError(f"Could not get a synth for {decomposition_mode}.")
