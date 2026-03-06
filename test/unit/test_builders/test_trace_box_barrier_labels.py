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

"""Test that the TraceBox annotation appends noise ref to barrier labels."""

from qiskit.circuit import QuantumCircuit

from samplomatic.annotations import InjectNoise, TraceBox, Twirl
from samplomatic.builders import pre_build


def _barrier_labels(template):
    """Extract barrier labels from a template circuit."""
    return [instr.operation.label for instr in template if instr.operation.name == "barrier"]


def test_trace_box_appends_noise_ref_to_barriers():
    """Test that TraceBox + InjectNoise causes barrier labels to include @noise=ref."""
    circuit = QuantumCircuit(2)
    with circuit.box([Twirl(), InjectNoise(ref="my_ref"), TraceBox()]):
        circuit.cx(0, 1)

    template_state, _ = pre_build(circuit)
    template = template_state.finalize()

    labels = _barrier_labels(template)
    box_labels = [
        label for label in labels if label is not None and label.startswith(("L", "M", "R"))
    ]
    assert len(box_labels) > 0, "Expected at least one box barrier"
    for label in box_labels:
        assert "@noise=my_ref" in label, f"Expected '@noise=my_ref' in barrier label '{label}'"


def test_no_trace_box_no_noise_ref_in_barriers():
    """Test that without TraceBox, barriers do NOT contain @ref."""
    circuit = QuantumCircuit(2)
    with circuit.box([Twirl(), InjectNoise(ref="my_ref")]):
        circuit.cx(0, 1)

    template_state, _ = pre_build(circuit)
    template = template_state.finalize()

    labels = _barrier_labels(template)
    for label in labels:
        if label is not None:
            assert "@" not in label, f"Unexpected '@' in barrier label '{label}'"


def test_trace_box_without_noise_ref_no_suffix():
    """Test that TraceBox without InjectNoise does not append anything."""
    circuit = QuantumCircuit(2)
    with circuit.box([Twirl(), TraceBox()]):
        circuit.cx(0, 1)

    template_state, _ = pre_build(circuit)
    template = template_state.finalize()

    labels = _barrier_labels(template)
    for label in labels:
        if label is not None:
            assert "@" not in label, f"Unexpected '@' in barrier label '{label}'"


def test_trace_box_ref_in_barriers():
    """Test that TraceBox.ref is included in barrier labels."""
    circuit = QuantumCircuit(2)
    with circuit.box([Twirl(), TraceBox(ref="my_box")]):
        circuit.cx(0, 1)

    template_state, _ = pre_build(circuit)
    template = template_state.finalize()

    labels = _barrier_labels(template)
    box_labels = [
        label for label in labels if label is not None and label.startswith(("L", "M", "R"))
    ]
    assert len(box_labels) > 0, "Expected at least one box barrier"
    for label in box_labels:
        assert "@trace=my_box" in label, f"Expected '@trace=my_box' in barrier label '{label}'"


def test_trace_box_ref_and_noise_ref_in_barriers():
    """Test that both TraceBox.ref and InjectNoise.ref appear in barrier labels."""
    circuit = QuantumCircuit(2)
    with circuit.box([Twirl(), InjectNoise(ref="my_ref"), TraceBox(ref="my_box")]):
        circuit.cx(0, 1)

    template_state, _ = pre_build(circuit)
    template = template_state.finalize()

    labels = _barrier_labels(template)
    box_labels = [
        label for label in labels if label is not None and label.startswith(("L", "M", "R"))
    ]
    assert len(box_labels) > 0, "Expected at least one box barrier"
    for label in box_labels:
        assert "@trace=my_box" in label, f"Expected '@trace=my_box' in barrier label '{label}'"
        assert "&noise=my_ref" in label, f"Expected '&noise=my_ref' in barrier label '{label}'"
