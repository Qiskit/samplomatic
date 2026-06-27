# This code is a Qiskit project.
#
# (C) Copyright IBM 2025, 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Test the ``generate_boxing_pass_manager`` function.

This function is more comprehensively tested in integration tests.
"""

import pytest
from qiskit.circuit import QuantumCircuit

from samplomatic.annotations import ChangeBasis, InjectNoise, Tag, Twirl
from samplomatic.transpiler import generate_boxing_pass_manager
from samplomatic.utils import get_annotation


def test_remove_barriers_deprecation():
    """Test deprecated values of the ``remove_barriers`` option."""
    circuit = QuantumCircuit(2)
    circuit.x(0)
    circuit.barrier()
    circuit.cx(0, 1)
    circuit.x(0)
    circuit.barrier()
    circuit.cx(0, 1)

    with pytest.warns(DeprecationWarning):
        pm_true = generate_boxing_pass_manager(remove_barriers=True)

    pm_immediately = generate_boxing_pass_manager(remove_barriers="immediately")
    assert pm_true.run(circuit) == pm_immediately.run(circuit)

    with pytest.warns(DeprecationWarning):
        pm_false = generate_boxing_pass_manager(remove_barriers=False)

    pm_never = generate_boxing_pass_manager(remove_barriers="never")
    assert pm_false.run(circuit) == pm_never.run(circuit)


def test_inject_noise_site_deprecation():
    """Test deprecated default values of the ``inject_noise_site`` option."""
    circuit = QuantumCircuit(2)
    circuit.cx(0, 1)
    circuit.cx(0, 1)

    with pytest.warns(FutureWarning):
        pm_none = generate_boxing_pass_manager()

    pm_before = generate_boxing_pass_manager(
        inject_noise_strategy="uniform_modification", inject_noise_site="before"
    )
    assert pm_none.run(circuit) == pm_before.run(circuit)


@pytest.mark.parametrize(
    "decomposition,measure_annotations", [("rzrx", "all"), ("rzsx", "change_basis")]
)
def test_decomposition(decomposition, measure_annotations):
    """Test the decomposition argument changes all decompositions."""
    circuit = QuantumCircuit(2)
    circuit.x(0)
    circuit.barrier()
    circuit.cx(0, 1)
    circuit.x(0)
    circuit.barrier()
    circuit.cx(0, 1)
    circuit.measure_all()

    pm = generate_boxing_pass_manager(
        decomposition=decomposition, measure_annotations=measure_annotations
    )
    transpiled_circuit = pm.run(circuit)

    for instr in transpiled_circuit:
        box = instr.operation

        if change_basis := get_annotation(box, ChangeBasis):
            assert change_basis.decomposition == decomposition

        if twirl := get_annotation(box, Twirl):
            assert twirl.decomposition == decomposition


@pytest.mark.parametrize("add_tags", ["unique_box", "unique_instance"])
def test_add_tags(add_tags):
    """Test that ``add_tags`` adds a :class:`~.Tag` to every box."""
    circuit = QuantumCircuit(2)
    circuit.cx(0, 1)
    circuit.cx(0, 1)
    circuit.measure_all()

    pm = generate_boxing_pass_manager(add_tags=add_tags)
    transpiled = pm.run(circuit)

    for instr in transpiled:
        tag = get_annotation(instr.operation, Tag)
        assert tag is not None
        assert tag.ref != ""


def test_add_tags_none_by_default():
    """Test that boxes have no :class:`~.Tag` annotation by default."""
    circuit = QuantumCircuit(2)
    circuit.cx(0, 1)
    circuit.measure_all()

    pm = generate_boxing_pass_manager()
    transpiled = pm.run(circuit)

    for instr in transpiled:
        assert get_annotation(instr.operation, Tag) is None


def test_add_tags_noise_ref():
    """Test ``add_tags='noise_ref'`` tags noisy boxes and skips noise-free boxes."""
    circuit = QuantumCircuit(2)
    circuit.cx(0, 1)
    circuit.measure_all()

    pm = generate_boxing_pass_manager(inject_noise_targets="gates", add_tags="noise_ref")
    transpiled = pm.run(circuit)

    for instr in transpiled:
        inject_noise = get_annotation(instr.operation, InjectNoise)
        tag = get_annotation(instr.operation, Tag)
        if inject_noise is not None:
            assert tag is not None
            assert tag.ref == inject_noise.ref
        else:
            assert tag is None


def test_active_qubits_none_is_no_op():
    """Test that ``active_qubits=None`` produces the same result as not specifying it."""
    circuit = QuantumCircuit(4)
    circuit.cz(0, 1)

    pm_default = generate_boxing_pass_manager(twirling_strategy="active")
    pm_explicit_none = generate_boxing_pass_manager(twirling_strategy="active", active_qubits=None)

    assert pm_default.run(circuit) == pm_explicit_none.run(circuit)


def test_active_qubits_empty_is_no_op():
    """Test that an empty ``active_qubits`` iterable is equivalent to ``None``."""
    circuit = QuantumCircuit(4)
    circuit.cz(0, 1)

    pm_default = generate_boxing_pass_manager(twirling_strategy="active")
    pm_empty = generate_boxing_pass_manager(twirling_strategy="active", active_qubits=[])

    assert pm_default.run(circuit) == pm_empty.run(circuit)


def test_active_qubits_rejects_non_int():
    """Test that non-integer qubit values raise ``TranspilerError`` at PM construction."""
    from qiskit.transpiler.exceptions import TranspilerError

    with pytest.raises(TranspilerError):
        generate_boxing_pass_manager(active_qubits=["q0"])


def test_active_qubits_accepts_generator():
    """Test that ``active_qubits`` can be a generator (is coerced to ``tuple`` defensively)."""
    pm = generate_boxing_pass_manager(twirling_strategy="active", active_qubits=(q for q in [0, 1]))

    circuit = QuantumCircuit(4)
    circuit.cz(2, 3)
    boxed = pm.run(circuit)

    twirl_boxes = [
        instr
        for instr in boxed
        if instr.operation.name == "box" and get_annotation(instr.operation, Twirl) is not None
    ]
    assert len(twirl_boxes) >= 1
    for instr in twirl_boxes:
        box_qubit_indices = {boxed.find_bit(q).index for q in instr.qubits}
        assert {0, 1}.issubset(box_qubit_indices)


def test_active_qubits_out_of_range_at_run_time():
    """Test that an out-of-range active qubit raises ``TranspilerError`` at ``pm.run()`` time."""
    from qiskit.transpiler.exceptions import TranspilerError

    pm = generate_boxing_pass_manager(active_qubits=[99])
    circuit = QuantumCircuit(3)
    circuit.cz(0, 1)

    with pytest.raises(TranspilerError):
        pm.run(circuit)


def test_active_qubits_boxes_include_qubits():
    """Test that every Twirl-annotated box includes the specified ``active_qubits``."""
    circuit = QuantumCircuit(4)
    circuit.cz(0, 1)  # only qubits 0 and 1 are active here

    pm = generate_boxing_pass_manager(twirling_strategy="active", active_qubits=[2, 3])
    boxed = pm.run(circuit)

    twirl_boxes = [
        instr
        for instr in boxed
        if instr.operation.name == "box" and get_annotation(instr.operation, Twirl) is not None
    ]
    assert len(twirl_boxes) >= 1
    for instr in twirl_boxes:
        box_qubit_indices = {boxed.find_bit(q).index for q in instr.qubits}
        assert {2, 3}.issubset(box_qubit_indices)


def test_active_qubits_combined_with_active_circuit():
    """Test that ``active_qubits`` is additive on top of the ``twirling_strategy``."""
    circuit = QuantumCircuit(5)
    circuit.cz(0, 1)
    circuit.cz(2, 3)

    # active_circuit will widen every box to {0, 1, 2, 3}; active_qubits adds qubit 4 on top.
    pm = generate_boxing_pass_manager(twirling_strategy="active_circuit", active_qubits=[4])
    boxed = pm.run(circuit)

    twirl_boxes = [
        instr
        for instr in boxed
        if instr.operation.name == "box" and get_annotation(instr.operation, Twirl) is not None
    ]
    assert len(twirl_boxes) >= 1
    for instr in twirl_boxes:
        box_qubit_indices = {boxed.find_bit(q).index for q in instr.qubits}
        assert {0, 1, 2, 3, 4}.issubset(box_qubit_indices)
