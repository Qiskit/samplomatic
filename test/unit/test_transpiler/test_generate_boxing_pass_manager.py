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

from samplomatic.annotations import ChangeBasis, Tag, Twirl
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
