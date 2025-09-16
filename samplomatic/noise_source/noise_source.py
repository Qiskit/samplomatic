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

"""NoiseSource"""

from typing import Protocol

import numpy as np
from qiskit.quantum_info import PauliLindbladMap, QubitSparsePauliList


class NoiseSource(Protocol):
    def get_rates(self, noise_ref: str) -> np.ndarray[np.float64]: ...
    def get_paulis(self, noise_ref: str) -> QubitSparsePauliList: ...
    def __contains__(self, noise_ref: str) -> bool: ...
    def __getitem__(self, noise_ref: str) -> PauliLindbladMap: ...
