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

"""Test the build method."""

import pytest

from samplomatic import build

from .utils import make_layered_circuit


class TestBuilder:
    """Test the `build` method."""

    @pytest.mark.parametrize(
        ("num_qubits", "num_gates"),
        [
            pytest.param(
                96,
                5_000,
                marks=pytest.mark.skipif(
                    "config.getoption('--performance-light')", reason="smoke test only"
                ),
            ),
            pytest.param(
                10,
                100,
                marks=pytest.mark.skipif(
                    "not config.getoption('--performance-light')", reason="performance test only"
                ),
            ),
        ],
    )
    def test_building_5k_circuit(self, benchmark, num_qubits, num_gates):
        """Test the build function for circuits with different numbers of qubits and gates."""
        num_boxes = num_gates // (num_qubits // 2)
        circuit = make_layered_circuit(num_qubits, num_boxes)

        template, _ = benchmark(build, circuit)

        assert template.num_qubits == num_qubits
