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

from samplomatic import build

from .utils import make_layered_circuit, make_noise_maps


class TestSample:
    """Test the `sample` method."""

    @pytest.mark.parametrize("num_qubits", [100])
    @pytest.mark.parametrize("num_gates", [5_000])
    @pytest.mark.parametrize("size", [1650])
    def test_sampling_5k_circuit(self, rng, benchmark, num_qubits, num_gates, size):
        """Test the sample function for circuits with different numbers of qubits and gates."""
        num_boxes = num_gates // (num_qubits // 2)
        circuit = make_layered_circuit(num_qubits, num_boxes)

        parameter_values = rng.random(len(circuit.parameters))

        template, samplex = build(circuit)
        samplex.finalize()
        samplex_output = benchmark(samplex.sample, parameter_values=parameter_values, size=size)

        assert circuit.num_parameters == 29700
        assert template.num_parameters == 30300
        assert samplex_output["parameter_values"].shape == (size, template.num_parameters)

    @pytest.mark.parametrize("num_qubits", [100])
    @pytest.mark.parametrize("num_gates", [5_000])
    @pytest.mark.parametrize("size", [1650])
    @pytest.mark.parametrize("scale", [-1.0])
    def test_sampling_noisy_circuit(self, rng, benchmark, num_qubits, num_gates, size, scale):
        """Test the sample function using ``noise_maps``."""
        num_boxes = num_gates // (num_qubits // 2)
        circuit = make_layered_circuit(num_qubits, num_boxes, inject_noise=True)
        even_layer_noise, odd_layer_noise = make_noise_maps(num_qubits)

        parameter_values = rng.random(len(circuit.parameters))
        noise_maps = {"even": even_layer_noise, "odd": odd_layer_noise}
        noise_scales = {"even": scale, "odd": scale}

        template, samplex = build(circuit)
        samplex.finalize()
        samplex_output = benchmark(
            samplex.sample,
            parameter_values=parameter_values,
            noise_maps=noise_maps,
            noise_scales=noise_scales,
            size=size,
        )

        assert circuit.num_parameters == 29700
        assert template.num_parameters == 30300
        assert samplex_output["parameter_values"].shape == (size, template.num_parameters)

    @pytest.mark.parametrize("num_qubits", [100])
    @pytest.mark.parametrize("num_gates", [5_000])
    @pytest.mark.parametrize("size", [1650])
    @pytest.mark.parametrize("local_scale", [2.0])
    def test_sampling_masked_noisy_circuit(
        self, rng, benchmark, num_qubits, num_gates, size, local_scale
    ):
        """Test the sample function using ``noise_maps`` with ``local_scale``."""
        num_boxes = num_gates // (num_qubits // 2)
        circuit = make_layered_circuit(num_qubits, num_boxes, inject_noise=True)
        even_noise, odd_noise = make_noise_maps(num_qubits)

        parameter_values = rng.random(len(circuit.parameters))
        noise_maps = {"even": even_noise, "odd": odd_noise}

        local_scales = {
            f"even_{idx}": [local_scale] * even_noise.num_terms for idx in range(num_boxes // 2)
        }
        local_scales.update(
            {f"odd_{idx}": [local_scale] * odd_noise.num_terms for idx in range(num_boxes // 2)}
        )

        template, samplex = build(circuit)
        samplex.finalize()
        samplex_output = benchmark(
            samplex.sample,
            parameter_values=parameter_values,
            noise_maps=noise_maps,
            local_scales=local_scales,
            size=size,
        )

        assert circuit.num_parameters == 29700
        assert template.num_parameters == 30300
        assert samplex_output["parameter_values"].shape == (size, template.num_parameters)
