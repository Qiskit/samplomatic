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

"""Integration tests utilities"""

import numpy as np
from qiskit.circuit import QuantumCircuit
from qiskit.quantum_info import hellinger_fidelity
from qiskit_aer import AerSimulator

from samplomatic.builders import pre_build

from ..utils import remove_boxes

REQUIRED_HELLINGER_FIDELITY = 0.985
NUM_RANDOMIZATIONS_PER_CIRCUIT = 10


def sample_simulate_and_compare_counts(circuit: QuantumCircuit, save_plot):
    """Helper function that builds the Samplex, samples using Qiskit Aer, and compares the counts
    against the original circuit, including Z2 corrections.

    While in many cases comparing the operators is sufficient to validate the sampling process,
    in some cases a simulation is needed (measurements, dynamic circuits). This function uses
    Qiskit Aer to simulate the original circuit and the twirled one, to validate that they're
    the same, using Hellinger fidelity.
    """
    save_plot(lambda: circuit.draw("mpl"), "Base Circuit", delayed=True)

    template, pre_samplex = pre_build(circuit)
    save_plot(lambda: template.template.draw("mpl"), "Template Circuit", delayed=True)
    save_plot(lambda: pre_samplex.draw(), "Unfinalized Pre-Samplex", delayed=True)

    samplex = pre_samplex.finalize()
    samplex.finalize()
    save_plot(lambda: pre_samplex.draw(), "Finalized Pre-Samplex", delayed=True)
    save_plot(lambda: samplex.draw(), "Samplex", delayed=True)

    circuit_params = np.random.random(len(circuit.parameters))
    original_circuit_counts = _simulate(remove_boxes(circuit), circuit_params)

    samplex_output = samplex.sample(
        parameter_values=circuit_params, size=NUM_RANDOMIZATIONS_PER_CIRCUIT
    )
    parameter_values = samplex_output["parameter_values"]
    measurement_flips = samplex_output.get(
        "measurement_flips", [None] * NUM_RANDOMIZATIONS_PER_CIRCUIT
    )
    for params, correction in zip(parameter_values, measurement_flips):
        twirled_circuit_counts = _simulate(template.template, params)
        if correction is not None:
            twirled_circuit_counts = _apply_bit_flips_correction(twirled_circuit_counts, correction)
        assert (
            hellinger_fidelity(original_circuit_counts, twirled_circuit_counts)
            > REQUIRED_HELLINGER_FIDELITY
        )


def _simulate(circuit: QuantumCircuit, circuit_params):
    """Helper function that runs the Aer simulator and returns the counts."""
    simulator = AerSimulator()
    assigned_circuit = circuit.assign_parameters(circuit_params)
    result = simulator.run(assigned_circuit).result()
    return result.get_counts()


def _apply_bit_flips_correction(original_counts, correction):
    """A helper function that applies the bit flip correction to the counts string."""
    corrected_counts = dict()
    correction = correction[::-1]  # Qiskit bitstrings use little-endian convention
    for key, value in original_counts.items():
        space_idxs = [ind for ind, ch in enumerate(key) if ch == " "]
        new_key_bool = np.bitwise_xor(np.array(list(key.replace(" ", "")), dtype=int), correction)
        new_key_bitstring = "".join(new_key_bool.astype(int).astype(str))
        new_key_bitstring = new_key_bitstring.rjust(len(key) - len(space_idxs), "0")
        for ind in space_idxs:
            new_key_bitstring = new_key_bitstring[:ind] + " " + new_key_bitstring[ind:]
        corrected_counts[new_key_bitstring] = value
    return corrected_counts
