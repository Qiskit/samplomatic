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

import numpy as np
import pytest
from qiskit.circuit import ParameterVector, QuantumCircuit
from qiskit.quantum_info import Operator, average_gate_fidelity

from samplomatic.annotations import VirtualType
from samplomatic.distributions import HaarU2
from samplomatic.exceptions import SamplexConstructionError
from samplomatic.samplex.interfaces import SamplexOutput
from samplomatic.samplex.nodes import CollectTemplateValues
from samplomatic.synths import RzSxSynth
from samplomatic.tensor_interface import TensorSpecification


def test_construction():
    """Test simple construction and simple attributes."""
    node = CollectTemplateValues(
        "template_values",
        [[0, 1, 3], [2, 4, 5]],
        "x",
        VirtualType.U2,
        [3, 2],
        RzSxSynth(),
    )

    assert node.outputs_to() == ["template_values"]
    assert node.num_parameters == 0
    assert node.num_subsystems == 2
    assert node.reads_from() == {"x": ({2, 3}, VirtualType.U2)}
    assert not node.writes_to() and not node.instantiates() and not node.removes()
    assert node.outgoing_register_type is None


def test_construction_fails():
    """Test the constructor fails when expected."""
    with pytest.raises(SamplexConstructionError, match="not compatible with 'pauli'"):
        CollectTemplateValues(
            "template_values", [[0, 1, 3], [2, 4, 5]], "x", VirtualType.PAULI, [3, 2], RzSxSynth()
        )

    with pytest.raises(SamplexConstructionError, match="expects the second axis to have size 3"):
        CollectTemplateValues(
            "template_values", [[0, 1], [2, 4]], "x", VirtualType.U2, [3, 2], RzSxSynth()
        )

    with pytest.raises(SamplexConstructionError, match=r"Expected .* 2 subsystems .* shape \(3,\)"):
        CollectTemplateValues(
            "template_values",
            [[0, 1, 3], [2, 4, 5]],
            "x",
            VirtualType.U2,
            [5, 6, 4],
            RzSxSynth(),
        )


def test_validate_fails():
    """Test the extra validation logic introduced by this node."""
    node = CollectTemplateValues(
        "template_values", [[0, 1, 3], [2, 4, 5]], "x", VirtualType.U2, [3, 2], RzSxSynth()
    )
    with pytest.raises(SamplexConstructionError, match="'u2' .* but found .* 'pauli'"):
        node.validate_and_update({"x": (10, VirtualType.PAULI)})


def test_collect(rng):
    """Test the collect method."""
    num_samples = 11
    outputs = SamplexOutput(
        [
            TensorSpecification(
                "template_values",
                (num_samples, 100),
                np.float32,
            )
        ]
    )
    x = HaarU2(10).sample(num_samples, rng)
    outputs["template_values"].ravel()[...] = np.linspace(0, 1, outputs["template_values"].size)
    original_template_values = outputs["template_values"].copy()

    # define and run the collection node
    node = CollectTemplateValues(
        "template_values",
        template_idxs_arr := [[0, 1, 3], [2, 4, 5]],
        "x",
        VirtualType.U2,
        x_idxs := [3, 2],
        synth := RzSxSynth(),
    )
    node.collect(registers := {"x": x.copy()}, outputs, rng)
    assert registers == {"x": x}

    # create a template circuit that we will bind against when checking correctness
    circuit = QuantumCircuit(1)
    for instr in synth.make_template(circuit.qubits, iter(ParameterVector("p", 10))):
        circuit.append(instr)

    # loop over indices corresponding to each subsystem
    for x_idx, template_idxs in zip(x_idxs, template_idxs_arr):
        # extract 2x2 unitaries for this subsystem, for all samples
        u2s_x = x.virtual_gates[x_idx]

        # loop over samples, and test unitary correctness on each one
        for sample_idx, u2_x in enumerate(u2s_x):
            values = outputs["template_values"][sample_idx, template_idxs]
            have = Operator(circuit.assign_parameters(values))
            expected = Operator(u2_x)
            assert np.isclose(average_gate_fidelity(have, expected), 1)

    # check that we didn't write anywhere that we shouldn't
    used_idxs = {idx for idxs in template_idxs_arr for idx in idxs}
    unused_template_idxs = sorted(set(range(outputs["template_values"].shape[1])) - used_idxs)
    assert np.array_equal(
        original_template_values[:, unused_template_idxs],
        outputs["template_values"][:, unused_template_idxs],
    )
