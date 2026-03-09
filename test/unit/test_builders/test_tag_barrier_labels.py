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

"""Test that annotations add trace information to barrier labels."""

from qiskit.circuit import QuantumCircuit

from samplomatic.annotations import InjectNoise, Tag, Twirl
from samplomatic.builders import pre_build


def _barrier_labels(template):
    """Extract barrier labels from a template circuit."""
    return [instr.operation.label for instr in template if instr.operation.name == "barrier"]


def test_inject_noise_ref_in_barriers():
    """Test that InjectNoise.ref is included in barrier labels."""
    circuit = QuantumCircuit(2)
    with circuit.box([Twirl(), InjectNoise(ref="my_ref")]):
        circuit.cx(0, 1)

    template_state, _ = pre_build(circuit)
    template = template_state.finalize()

    labels = _barrier_labels(template)
    for label in labels:
        if label is not None:
            assert (
                "@inject_noise=my_ref" in label
            ), f"Expected '@inject_noise=my_ref' in label '{label}'"


def test_tag_ref_in_barriers():
    """Test that Tag.ref is included in barrier labels."""
    circuit = QuantumCircuit(2)
    with circuit.box([Twirl(), Tag(ref="my_box")]):
        circuit.cx(0, 1)

    template_state, _ = pre_build(circuit)
    template = template_state.finalize()

    labels = _barrier_labels(template)
    box_labels = [
        label for label in labels if label is not None and label.startswith(("L", "M", "R"))
    ]
    assert len(box_labels) > 0, "Expected at least one box barrier"
    for label in box_labels:
        assert "@tag=my_box" in label, f"Expected '@tag=my_box' in label '{label}'"


def test_tag_ref_and_noise_ref_in_barriers():
    """Test that both Tag.ref and InjectNoise.ref appear in barrier labels."""
    circuit = QuantumCircuit(2)
    with circuit.box([Twirl(), InjectNoise(ref="my_ref"), Tag(ref="my_box")]):
        circuit.cx(0, 1)

    template_state, _ = pre_build(circuit)
    template = template_state.finalize()

    labels = _barrier_labels(template)
    box_labels = [
        label for label in labels if label is not None and label.startswith(("L", "M", "R"))
    ]
    assert len(box_labels) > 0, "Expected at least one box barrier"
    for label in box_labels:
        assert "tag=my_box" in label, f"Expected 'tag=my_box' in barrier label '{label}'"
        assert (
            "inject_noise=my_ref" in label
        ), f"Expected 'inject_noise=my_ref' in barrier label '{label}'"
        assert label.count("@") == 1
        assert label.count("&") == 1
