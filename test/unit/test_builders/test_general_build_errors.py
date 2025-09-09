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

"""Testing of error raising during building process.

Some build errors are hard to replicate without going through the entire build process.
This file is meant for such cases."""

import pytest
from qiskit.circuit import Parameter, QuantumCircuit

from samplomatic import Twirl
from samplomatic.builders import pre_build
from samplomatic.exceptions import SamplexBuildError


class TestGeneralBuildErrors:
    def _pre_build_and_assert_error(self, circuit, error_type, message):
        with pytest.raises(error_type, match=message):
            pre_build(circuit)

    def test_nonclifford_between_left_right_boxes(self):
        circuit = QuantumCircuit(1)
        with circuit.box([Twirl(dressing="left")]):
            circuit.noop(0)
        circuit.rx(1.2, 0)
        with circuit.box([Twirl(dressing="right")]):
            circuit.noop(0)
        self._pre_build_and_assert_error(
            circuit,
            SamplexBuildError,
            "Cannot have non-clifford gate between a left-dressed box and a right-dressed box",
        )

    def test_parametric_nonclifford_between_left_right_boxes(self):
        circuit = QuantumCircuit(1)
        with circuit.box([Twirl(dressing="left")]):
            circuit.noop(0)
        circuit.rz(Parameter("a"), 0)
        with circuit.box([Twirl(dressing="right")]):
            circuit.noop(0)
        self._pre_build_and_assert_error(
            circuit,
            SamplexBuildError,
            "Cannot have non-clifford gate between a left-dressed box and a right-dressed box",
        )
