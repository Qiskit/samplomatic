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

"""Tests for annotation mapping utilities."""

import pytest
from qiskit.circuit import QuantumCircuit

from samplomatic.annotations import ChangeBasis, InjectNoise, Twirl
from samplomatic.utils import (
    extend_annotations,
    filter_annotations,
    map_annotations,
    replace_annotations,
    strip_annotations,
)


@pytest.fixture
def two_box_circuit():
    """Return a circuit with two boxes having different annotations."""
    circuit = QuantumCircuit(2)
    with circuit.box([Twirl(), InjectNoise("ref1")]):
        circuit.cx(0, 1)
    with circuit.box([ChangeBasis(ref="cb")]):
        circuit.h(0)
    return circuit


@pytest.fixture
def plain_circuit():
    """Return a circuit with a non-box gate and one annotated box."""
    circuit = QuantumCircuit(2)
    circuit.h(0)
    with circuit.box([Twirl()]):
        circuit.cx(0, 1)
    circuit.cx(0, 1)
    return circuit


class TestMapAnnotations:
    """Tests for ``map_annotations``."""

    def test_returns_new_circuit(self, two_box_circuit):
        """map_annotations returns a new circuit object."""
        result = map_annotations(two_box_circuit, lambda anns: anns)
        assert result is not two_box_circuit

    def test_original_not_mutated(self, two_box_circuit):
        """Original circuit annotations are not mutated."""
        original_annots = [list(instr.operation.annotations) for instr in two_box_circuit.data]
        map_annotations(two_box_circuit, lambda _: [Twirl()])
        for i, instr in enumerate(two_box_circuit.data):
            assert list(instr.operation.annotations) == original_annots[i]

    def test_non_box_instructions_preserved(self, plain_circuit):
        """Non-box instructions pass through unchanged."""
        result = map_annotations(plain_circuit, lambda _: [])
        assert len(result.data) == len(plain_circuit.data)
        for orig, new in zip(plain_circuit.data, result.data):
            if orig.operation.name != "box":
                assert orig.operation == new.operation
                assert orig.qubits == new.qubits

    def test_callable_receives_annotations(self, two_box_circuit):
        """Callable is invoked with the correct annotation lists."""
        seen = []
        map_annotations(two_box_circuit, lambda anns: seen.append(list(anns)) or anns)
        assert len(seen) == 2
        assert any(isinstance(a, Twirl) for a in seen[0])
        assert any(isinstance(a, InjectNoise) for a in seen[0])
        assert any(isinstance(a, ChangeBasis) for a in seen[1])

    def test_replaces_annotations(self, two_box_circuit):
        """Returned annotations from callable appear on the new circuit."""
        new_twirl = Twirl(group="local_c1")
        result = map_annotations(two_box_circuit, lambda _: [new_twirl])
        for instr in result.data:
            assert list(instr.operation.annotations) == [new_twirl]

    def test_qubits_preserved(self, two_box_circuit):
        """Qubit assignments on box instructions are preserved."""
        result = map_annotations(two_box_circuit, lambda anns: anns)
        for orig, new in zip(two_box_circuit.data, result.data):
            assert orig.qubits == new.qubits

    def test_box_body_preserved(self, two_box_circuit):
        """Box bodies are preserved by reference."""
        result = map_annotations(two_box_circuit, lambda anns: anns)
        for orig, new in zip(two_box_circuit.data, result.data):
            assert orig.operation.body is new.operation.body


class TestStripAnnotations:
    """Tests for ``strip_annotations``."""

    def test_removes_all(self, two_box_circuit):
        """All annotations are removed from every box."""
        result = strip_annotations(two_box_circuit)
        for instr in result.data:
            assert list(instr.operation.annotations) == []

    def test_non_box_preserved(self, plain_circuit):
        """Non-box instructions are preserved."""
        result = strip_annotations(plain_circuit)
        assert len(result.data) == len(plain_circuit.data)


class TestFilterAnnotations:
    """Tests for ``filter_annotations``."""

    def test_keeps_matching_type(self, two_box_circuit):
        """Only annotations of the specified type are kept."""
        result = filter_annotations(two_box_circuit, Twirl)
        box_annotations = [list(instr.operation.annotations) for instr in result.data]
        assert all(isinstance(a, Twirl) for anns in box_annotations for a in anns)

    def test_removes_non_matching(self, two_box_circuit):
        """InjectNoise is removed when filtering for Twirl only."""
        result = filter_annotations(two_box_circuit, Twirl)
        for instr in result.data:
            assert not any(isinstance(a, InjectNoise) for a in instr.operation.annotations)

    def test_keeps_multiple_types(self, two_box_circuit):
        """Multiple types can be kept with a tuple."""
        result = filter_annotations(two_box_circuit, (Twirl, InjectNoise))
        for instr in result.data:
            assert not any(isinstance(a, ChangeBasis) for a in instr.operation.annotations)

    def test_empty_when_no_match(self, two_box_circuit):
        """Boxes with no matching annotations get an empty list."""
        circuit = QuantumCircuit(2)
        with circuit.box([ChangeBasis(ref="cb")]):
            circuit.cx(0, 1)
        result = filter_annotations(circuit, Twirl)
        assert list(result.data[0].operation.annotations) == []


class TestExtendAnnotations:
    """Tests for ``extend_annotations``."""

    def test_appends_annotation(self, two_box_circuit):
        """Given annotation is appended to every box."""
        noise = InjectNoise("new_ref")
        result = extend_annotations(two_box_circuit, noise)
        for instr in result.data:
            assert instr.operation.annotations[-1] is noise

    def test_original_annotations_kept(self, two_box_circuit):
        """Original annotations remain before the appended ones."""
        noise = InjectNoise("new_ref")
        result = extend_annotations(two_box_circuit, noise)
        for orig, new in zip(two_box_circuit.data, result.data):
            orig_anns = list(orig.operation.annotations)
            new_anns = list(new.operation.annotations)
            assert new_anns[: len(orig_anns)] == orig_anns

    def test_multiple_annotations_appended(self):
        """Multiple annotations can be appended at once."""
        circuit = QuantumCircuit(2)
        with circuit.box([]):
            circuit.cx(0, 1)
        twirl = Twirl()
        noise = InjectNoise("ref")
        result = extend_annotations(circuit, twirl, noise)
        assert list(result.data[0].operation.annotations) == [twirl, noise]


class TestReplaceAnnotations:
    """Tests for ``replace_annotations``."""

    def test_replaces_matching(self):
        """Matching annotations are replaced by the callable's return value."""
        circuit = QuantumCircuit(2)
        with circuit.box([Twirl(group="pauli")]):
            circuit.cx(0, 1)
        new_twirl = Twirl(group="local_c1")
        result = replace_annotations(
            circuit, lambda a: [new_twirl] if isinstance(a, Twirl) else [a]
        )
        assert list(result.data[0].operation.annotations) == [new_twirl]

    def test_deletes_when_empty_list(self):
        """Annotations for which fn returns [] are removed."""
        circuit = QuantumCircuit(2)
        twirl = Twirl()
        noise = InjectNoise("ref")
        with circuit.box([twirl, noise]):
            circuit.cx(0, 1)
        result = replace_annotations(circuit, lambda a: [] if isinstance(a, InjectNoise) else [a])
        assert list(result.data[0].operation.annotations) == [twirl]

    def test_all_annotations_visited(self):
        """fn is called for every annotation, not just the first match."""
        circuit = QuantumCircuit(2)
        t1 = Twirl(group="pauli")
        t2 = Twirl(group="local_c1")
        with circuit.box([t1, t2]):
            circuit.cx(0, 1)
        new_twirl = Twirl(group="balanced_pauli")
        result = replace_annotations(
            circuit, lambda a: [new_twirl] if isinstance(a, Twirl) else [a]
        )
        anns = list(result.data[0].operation.annotations)
        assert anns == [new_twirl, new_twirl]

    def test_passthrough_unchanged(self):
        """Returning the annotation in a list leaves it in place."""
        circuit = QuantumCircuit(2)
        change_basis = ChangeBasis(ref="cb")
        with circuit.box([change_basis]):
            circuit.cx(0, 1)
        result = replace_annotations(circuit, lambda a: [a])
        assert list(result.data[0].operation.annotations) == [change_basis]

    def test_mixed_replace_and_delete(self):
        """fn can replace some annotations and delete others in the same box."""
        circuit = QuantumCircuit(2)
        noise = InjectNoise("ref")
        old_twirl = Twirl(group="pauli")
        with circuit.box([noise, old_twirl]):
            circuit.cx(0, 1)
        new_twirl = Twirl(group="local_c1")
        result = replace_annotations(circuit, lambda a: [new_twirl] if isinstance(a, Twirl) else [])
        anns = list(result.data[0].operation.annotations)
        assert anns == [new_twirl]

    def test_one_to_many_expansion(self):
        """fn can expand one annotation into multiple."""
        circuit = QuantumCircuit(2)
        twirl = Twirl()
        with circuit.box([twirl]):
            circuit.cx(0, 1)
        noise = InjectNoise("ref")
        result = replace_annotations(circuit, lambda a: [a, noise] if isinstance(a, Twirl) else [a])
        assert list(result.data[0].operation.annotations) == [twirl, noise]
