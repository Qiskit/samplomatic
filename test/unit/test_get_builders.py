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

import pytest
from qiskit.circuit import Annotation, BoxOp, CircuitInstruction, QuantumCircuit, Qubit

from samplomatic.annotations import DressingMode, Twirl
from samplomatic.builders.get_builders import get_builders, twirl_parser
from samplomatic.builders.specs import CollectionSpec, EmissionSpec
from samplomatic.exceptions import BuildError
from samplomatic.partition import QubitPartition
from samplomatic.synths import RzSxSynth


def test_get_builders_errors():
    """Test the errors when getting builders."""
    circuit = QuantumCircuit(1)
    op = CircuitInstruction(BoxOp(circuit, annotations=[Annotation()]))
    with pytest.raises(BuildError, match="Cannot get a builder"):
        get_builders(op, circuit.qubits)

    op = CircuitInstruction(BoxOp(circuit, annotations=[Twirl(), Twirl()]))
    with pytest.raises(BuildError, match="Cannot specify more than one"):
        get_builders(op, circuit.qubits)


def test_twirl_parser_errors():
    """Test the errors when parsing a twirl annotation."""
    qubits = QubitPartition(1, [(Qubit(),)])
    collection = CollectionSpec(qubits, dressing=DressingMode.LEFT, synth=RzSxSynth())
    emission = EmissionSpec(qubits, dressing=DressingMode.LEFT)

    with pytest.raises(BuildError, match="Cannot use different dressings"):
        twirl_parser(Twirl(dressing="right"), collection, emission)

    with pytest.raises(BuildError, match="Cannot use different synthesizers"):
        twirl_parser(Twirl(decomposition="rzrx"), collection, emission)
