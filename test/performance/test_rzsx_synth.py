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

"""Benchmark synthesizers"""

import pytest

from samplomatic.distributions import HaarU2
from samplomatic.synths import RzRxSynth, RzSxSynth


class TestTemplateValueGeneration:
    """Test the performance of generating template values."""

    @pytest.mark.parametrize(
        ("num_subsystems", "num_randomizations"),
        [
            pytest.param(
                200,
                10_000,
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
    def test_rzsx_generate_template_values(
        self, rng, benchmark, num_subsystems, num_randomizations
    ):
        """Benchmark generate_template_values with a large U2Register."""
        register = HaarU2(num_subsystems).sample(num_randomizations, rng)
        synth = RzSxSynth()
        result = benchmark(synth.generate_template_values, register)
        assert result.shape == (num_subsystems, num_randomizations, 3)

    @pytest.mark.parametrize(
        ("num_subsystems", "num_randomizations"),
        [
            pytest.param(
                200,
                10_000,
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
    def test_rzrx_generate_template_values(
        self, rng, benchmark, num_subsystems, num_randomizations
    ):
        """Benchmark generate_template_values with a large U2Register."""
        register = HaarU2(num_subsystems).sample(num_randomizations, rng)
        synth = RzRxSynth()
        result = benchmark(synth.generate_template_values, register)
        assert result.shape == (num_subsystems, num_randomizations, 3)
