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

"""Test the sample method."""

import pytest
from qiskit.quantum_info import QubitSparsePauliList

from samplomatic import build

from .utils import make_layered_circuit, make_noise_maps


class TestSample:
    """Test the `sample` method."""

    @pytest.mark.parametrize(
        ("num_qubits", "num_gates", "num_randomizations"),
        [
            pytest.param(
                96,
                5_000,
                1650,
                marks=pytest.mark.skipif(
                    "config.getoption('--performance-light')", reason="smoke test only"
                ),
            ),
            pytest.param(
                10,
                100,
                10,
                marks=pytest.mark.skipif(
                    "not config.getoption('--performance-light')", reason="performance test only"
                ),
            ),
        ],
    )
    def test_sampling_5k_circuit(self, rng, benchmark, num_qubits, num_gates, num_randomizations):
        """Test the sample function for circuits with different numbers of qubits and gates."""
        num_boxes = num_gates // (num_qubits // 2)
        circuit = make_layered_circuit(num_qubits, num_boxes)

        template, samplex = build(circuit)
        samplex_input = samplex.inputs().bind(parameter_values=rng.random(len(circuit.parameters)))
        samplex_output = benchmark(
            samplex.sample, samplex_input, num_randomizations=num_randomizations
        )

        assert template.num_parameters == (num_boxes + 1) * num_qubits * 3
        assert samplex_output["parameter_values"].shape == (
            num_randomizations,
            template.num_parameters,
        )

    @pytest.mark.parametrize(
        ("num_qubits", "num_gates", "num_randomizations"),
        [
            pytest.param(
                96,
                5_000,
                1650,
                marks=pytest.mark.skipif(
                    "config.getoption('--performance-light')", reason="smoke test only"
                ),
            ),
            pytest.param(
                10,
                100,
                10,
                marks=pytest.mark.skipif(
                    "not config.getoption('--performance-light')", reason="performance test only"
                ),
            ),
        ],
    )
    @pytest.mark.parametrize("scale", [-1.0])
    def test_sampling_noisy_circuit(
        self, rng, benchmark, num_qubits, num_gates, num_randomizations, scale
    ):
        """Test the sample function using ``noise_maps``."""
        num_boxes = num_gates // (num_qubits // 2)
        circuit = make_layered_circuit(num_qubits, num_boxes, inject_noise=True)
        even_noise, odd_noise = make_noise_maps(num_qubits)

        even_paulis = QubitSparsePauliList.from_sparse_list(
            [(pauli, idxs) for pauli, idxs, _ in even_noise.to_sparse_list()], even_noise.num_qubits
        )
        odd_paulis = QubitSparsePauliList.from_sparse_list(
            [(pauli, idxs) for pauli, idxs, _ in odd_noise.to_sparse_list()], odd_noise.num_qubits
        )

        template, samplex = build(circuit)
        samplex_input = samplex.inputs({"even": even_paulis, "odd": odd_paulis}).bind(
            parameter_values=rng.random(len(circuit.parameters)),
            noise_maps={"rates.even": even_noise.rates, "rates.odd": odd_noise.rates},
            noise_scales={"even": scale, "odd": scale},
        )
        samplex_output = benchmark(
            samplex.sample,
            samplex_input,
            num_randomizations=num_randomizations,
        )

        assert template.num_parameters == (num_boxes + 1) * num_qubits * 3
        assert samplex_output["parameter_values"].shape == (
            num_randomizations,
            template.num_parameters,
        )

    @pytest.mark.parametrize(
        ("num_qubits", "num_gates", "num_randomizations"),
        [
            pytest.param(
                96,
                5_000,
                1650,
                marks=pytest.mark.skipif(
                    "config.getoption('--performance-light')", reason="smoke test only"
                ),
            ),
            pytest.param(
                10,
                100,
                10,
                marks=pytest.mark.skipif(
                    "not config.getoption('--performance-light')", reason="performance test only"
                ),
            ),
        ],
    )
    @pytest.mark.parametrize("local_scale", [2.0])
    def test_sampling_masked_noisy_circuit(
        self, rng, benchmark, num_qubits, num_gates, num_randomizations, local_scale
    ):
        """Test the sample function using ``noise_maps`` with ``local_scale``."""
        num_boxes = num_gates // (num_qubits // 2)
        circuit = make_layered_circuit(num_qubits, num_boxes, inject_noise=True)
        even_noise, odd_noise = make_noise_maps(num_qubits)

        even_paulis = QubitSparsePauliList.from_sparse_list(
            [(pauli, idxs) for pauli, idxs, _ in even_noise.to_sparse_list()], even_noise.num_qubits
        )
        odd_paulis = QubitSparsePauliList.from_sparse_list(
            [(pauli, idxs) for pauli, idxs, _ in odd_noise.to_sparse_list()], odd_noise.num_qubits
        )

        local_scales = {
            "even": [local_scale] * even_noise.num_terms,
            "odd": [local_scale] * odd_noise.num_terms,
        }

        template, samplex = build(circuit)
        samplex_input = samplex.inputs({"even": even_paulis, "odd": odd_paulis}).bind(
            parameter_values=rng.random(len(circuit.parameters)),
            noise_maps={"rates.even": even_noise.rates, "rates.odd": odd_noise.rates},
            local_scales=local_scales,
        )
        samplex_output = benchmark(
            samplex.sample,
            samplex_input,
            num_randomizations=num_randomizations,
        )

        assert template.num_parameters == (num_boxes + 1) * num_qubits * 3
        assert samplex_output["parameter_values"].shape == (
            num_randomizations,
            template.num_parameters,
        )
