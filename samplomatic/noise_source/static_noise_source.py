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

"""StaticNoiseSource"""

from collections.abc import Mapping

import numpy as np
from qiskit.quantum_info import PauliLindbladMap, QubitSparsePauliList


class StaticNoiseSource(Mapping):
    """A static noise source that implements the :class:`~.NoiseSource` protocol.

    Args:
        noise_maps: A map from noise references to :class:`qiskit.quantum_info.PauliLindbladMap`s.
    """

    def __init__(self, noise_maps: dict[str, PauliLindbladMap]):
        self._noise_maps = noise_maps

    def get_paulis(self, noise_ref: str) -> QubitSparsePauliList:
        """Return the Paulis associated with the given noise reference.

        Args:
            noise_ref: The noise reference.

        Returns:
            A qubit sparse Pauli list.
        """
        noise_map = self[noise_ref]
        return QubitSparsePauliList.from_sparse_list(
            [(pauli, idx) for pauli, idx, _ in noise_map.to_sparse_list()], noise_map.num_qubits
        )

    def get_rates(self, noise_ref: str) -> np.ndarray[np.float64]:
        """Return the rates associated with the given noise reference.

        Args:
            noise_ref: The noise reference.

        Returns:
            An array containg the rates.
        """
        return self[noise_ref].rates

    def __contains__(self, noise_ref: str) -> bool:
        return noise_ref in self._noise_maps

    def __getitem__(self, noise_ref: str) -> PauliLindbladMap:
        if (noise_map := self._noise_maps.get(noise_ref)) is None:
            raise ValueError(f"'{noise_ref}' is not present in this noise source.")
        return noise_map

    def __iter__(self):
        return iter(self._noise_maps)

    def __len__(self):
        return len(self._noise_maps)
