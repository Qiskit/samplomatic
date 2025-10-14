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
from qiskit.primitives import BitArray
from qiskit.quantum_info import hellinger_fidelity
from qiskit.transpiler import PassManager
from qiskit_aer.primitives import SamplerV2

from samplomatic.builders import pre_build
from samplomatic.transpiler.passes import InlineBoxes

REQUIRED_HELLINGER_FIDELITY = 0.985
NUM_RANDOMIZATIONS_PER_CIRCUIT = 10


def sample_simulate_and_compare_counts(circuit: QuantumCircuit, save_plot):
    """Build the Samplex, sample using Qiskit Aer, and compare the counts.

    Counts are compared against the original circuit, including Z2 corrections.

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
    original_circuit_result = _simulate(PassManager([InlineBoxes()]).run(circuit), circuit_params)

    samplex_input = samplex.inputs().bind()
    if len(circuit_params) > 0:
        samplex_input.bind(parameter_values=circuit_params)
    samplex_output = samplex.sample(
        samplex_input, num_randomizations=NUM_RANDOMIZATIONS_PER_CIRCUIT
    )
    parameter_values = samplex_output["parameter_values"]

    twirled_circuit_result = _simulate(template.template, parameter_values)
    for creg in circuit.cregs:
        creg_name = creg.name
        twirled_creg_data = getattr(twirled_circuit_result.data, creg_name)
        original_creg_data = getattr(original_circuit_result.data, creg_name)

        if "measurement_flips." + creg.name in samplex_output:
            flips = samplex_output["measurement_flips." + creg.name]
            corrected_bool_array = np.logical_xor(
                np.unpackbits(twirled_creg_data.array, axis=-1, bitorder="little", count=creg.size),
                flips,
            )

            twirled_circuit_counts = BitArray.from_bool_array(
                corrected_bool_array, order="little"
            ).get_counts()
        else:
            twirled_circuit_counts = twirled_creg_data.get_counts()

        print(twirled_circuit_counts)
        print(original_creg_data.get_counts())
        assert (
            hellinger_fidelity(original_creg_data.get_counts(), twirled_circuit_counts)
            > REQUIRED_HELLINGER_FIDELITY
        )


def _simulate(circuit: QuantumCircuit, circuit_params):
    """Run the Aer simulator and returns the result."""
    sampler = SamplerV2()
    print(circuit_params.shape)
    print(len(circuit.parameters))
    for inst in circuit:
        print(inst)
        print(inst.params)
    return sampler.run([(circuit, circuit_params, 1000)]).result()[0]
