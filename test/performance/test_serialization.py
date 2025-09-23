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


"""Test serialization."""

import pytest

from samplomatic import build
from samplomatic.samplex.samplex_serialization import samplex_from_json, samplex_to_json

from .utils import make_layered_circuit


@pytest.mark.parametrize(
    ("num_qubits", "num_gates"),
    [
        pytest.param(
            100,
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
def test_serialize_noisy_circuit(rng, benchmark, num_qubits, num_gates):
    """Test the speed of serializing a samplex."""
    num_boxes = num_gates // (num_qubits // 2)
    circuit = make_layered_circuit(num_qubits, num_boxes, inject_noise=True)

    _, samplex = build(circuit)
    benchmark(samplex_to_json, samplex)


@pytest.mark.parametrize(
    ("num_qubits", "num_gates"),
    [
        pytest.param(
            100,
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
def test_deserialize_noisy_circuit(rng, benchmark, num_qubits, num_gates):
    """Test the speed of deserializing a samplex."""
    num_boxes = num_gates // (num_qubits // 2)
    circuit = make_layered_circuit(num_qubits, num_boxes, inject_noise=True)

    _, samplex = build(circuit)
    samplex_json = samplex_to_json(samplex)
    benchmark(samplex_from_json, samplex_json)
