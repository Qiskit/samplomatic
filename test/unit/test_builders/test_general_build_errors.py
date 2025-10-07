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
This file is meant for such cases.
"""

import pytest
from qiskit.circuit import QuantumCircuit
from qiskit.circuit.classical import expr

from samplomatic import Twirl
from samplomatic.builders import pre_build
from samplomatic.exceptions import BuildError, SamplexBuildError


class TestGeneralBuildErrors:
    def test_no_propagation_through_conditional_error(self):
        """Verify that an error is raised if a virtual gate reaches a conditional."""
        circuit = QuantumCircuit(2, 3)
        with circuit.box([Twirl(dressing="left")]):
            circuit.x(0)
            circuit.measure(1, circuit.clbits[0])
        with circuit.if_test((circuit.clbits[0], 1)):
            circuit.x(1)

        with pytest.raises(BuildError, match="Cannot propagate through if_else instruction."):
            pre_build(circuit)

    def test_bad_order_right_box(self):
        """Verify an error is raised if a gate follows a conditional in a right dressed box."""
        circuit = QuantumCircuit(2, 3)
        with circuit.box([Twirl(dressing="left")]):
            circuit.noop(1)
        with circuit.box([Twirl(dressing="right")]):
            with circuit.if_test((circuit.clbits[0], 1)):
                circuit.sx(1)
            circuit.sx(1)

        with pytest.raises(
            RuntimeError, match="Cannot handle instructions to the right of if-else ops."
        ):
            pre_build(circuit)

    def test_bad_order_left_box(self):
        """Verify an error is raised if a conditional follows a gate in a left dressed box."""
        circuit = QuantumCircuit(2, 3)
        with circuit.box([Twirl(dressing="left")]):
            circuit.x(1)
            with circuit.if_test((circuit.clbits[0], 1)):
                circuit.sx(1)

        with pytest.raises(
            SamplexBuildError, match="No instruction can appear before a conditional"
        ):
            pre_build(circuit)

    def test_entangler_bad_order_left_box(self):
        """Verify that an error is raised if a entanglers appear in bad order."""
        circuit = QuantumCircuit(2, 3)
        with circuit.box([Twirl(dressing="left")]):
            with circuit.if_test((circuit.clbits[0], 1)):
                circuit.cx(0, 1)
            circuit.x(0)

        with pytest.raises(
            RuntimeError,
            match="Cannot handle single-qubit gate to the right of entangler when dressing=left",
        ):
            pre_build(circuit)

        # Now for the else branch
        circuit = QuantumCircuit(2, 3)
        with circuit.box([Twirl(dressing="left")]):
            with circuit.if_test((circuit.clbits[0], 1)) as _else:
                circuit.x(0)
            with _else:
                circuit.cx(0, 1)
            circuit.x(0)

        with pytest.raises(
            RuntimeError,
            match="Cannot handle single-qubit gate to the right of entangler when dressing=left",
        ):
            pre_build(circuit)

    def test_twirled_clbit_in_passthroguh_condition_error(self):
        """Test for error if a passthrough conditional depends on a twirled classical bit."""
        circuit = QuantumCircuit(2, 2)
        with circuit.box([Twirl(dressing="left")]):
            circuit.measure(0, 0)
        with circuit.box([Twirl(dressing="left")]):
            circuit.noop(0)
        with circuit.box([Twirl(dressing="right")]):
            circuit.noop(0)
        with circuit.if_test((circuit.clbits[0], 1)):
            circuit.sx(0)

        with pytest.raises(
            BuildError, match="Cannot use twirled classical bits in classical conditions"
        ):
            pre_build(circuit)

    def test_twirled_clregister_in_passthrough_condition_error(self):
        """Test for error if a passthrough conditional depends on a twirled classical register."""
        circuit = QuantumCircuit(2, 2)
        with circuit.box([Twirl(dressing="left")]):
            circuit.measure(0, 0)
        with circuit.box([Twirl(dressing="left")]):
            circuit.noop(0)
        with circuit.box([Twirl(dressing="right")]):
            circuit.noop(0)
        with circuit.if_test((circuit.cregs[0], 1)):
            circuit.sx(0)

        with pytest.raises(
            BuildError, match="Cannot use twirled classical bits in classical conditions"
        ):
            pre_build(circuit)

    def test_twirled_clbit_in_right_condition_error(self):
        """Test for error if a right-box conditional depends on a twirled classical bit."""
        circuit = QuantumCircuit(2, 2)
        with circuit.box([Twirl(dressing="left")]):
            circuit.measure(0, 0)
        with circuit.box([Twirl(dressing="left")]):
            circuit.noop(0)
        with circuit.box([Twirl(dressing="right")]):
            with circuit.if_test((circuit.clbits[0], 1)):
                circuit.sx(0)

        with pytest.raises(
            BuildError, match="Cannot use twirled classical bits in classical conditions"
        ):
            pre_build(circuit)

    def test_twirled_clregister_in_right_condition_error(self):
        """Test for error if a right-box conditional depends on a twirled classical register."""
        circuit = QuantumCircuit(2, 2)
        with circuit.box([Twirl(dressing="left")]):
            circuit.measure(0, 0)
        with circuit.box([Twirl(dressing="left")]):
            circuit.noop(0)
        with circuit.box([Twirl(dressing="right")]):
            with circuit.if_test((circuit.cregs[0], 1)):
                circuit.sx(0)

        with pytest.raises(
            BuildError, match="Cannot use twirled classical bits in classical conditions"
        ):
            pre_build(circuit)

    def test_twirled_clbit_in_left_condition_error(self):
        """Test for error if a left-box conditional depends on a twirled classical bit."""
        circuit = QuantumCircuit(2, 2)
        with circuit.box([Twirl(dressing="left")]):
            circuit.measure(0, 0)
        with circuit.box([Twirl(dressing="left")]):
            with circuit.if_test((circuit.clbits[0], 1)):
                circuit.sx(0)

        with pytest.raises(
            BuildError, match="Cannot use twirled classical bits in classical conditions"
        ):
            pre_build(circuit)

    def test_twirled_clregister_in_left_condition_error(self):
        """Test for error if a left-box conditional depends on a twirled classical register."""
        circuit = QuantumCircuit(2, 2)
        with circuit.box([Twirl(dressing="left")]):
            circuit.measure(0, 0)
        with circuit.box([Twirl(dressing="left")]):
            with circuit.if_test((circuit.cregs[0], 1)):
                circuit.sx(0)

        with pytest.raises(
            BuildError, match="Cannot use twirled classical bits in classical conditions"
        ):
            pre_build(circuit)

    def test_twirled_expr_in_left_condition_error(self):
        """Test for an error if a left-box conditional depends on a twirled classical expression."""
        circuit = QuantumCircuit(2, 2)
        with circuit.box([Twirl(dressing="left")]):
            circuit.measure(0, 0)
        with circuit.box([Twirl(dressing="left")]):
            with circuit.if_test(
                expr.logic_and(expr.logic_not(circuit.clbits[0]), circuit.clbits[1])
            ):
                circuit.sx(0)

        with pytest.raises(
            BuildError, match="Cannot use twirled classical bits in classical conditions"
        ):
            pre_build(circuit)

    def test_repeated_twirled_clbit_error(self):
        """Verify that an error is raised if the same clbit is used more than once for twirling"""
        circuit = QuantumCircuit(2, 3)
        with circuit.box([Twirl(dressing="left")]):
            circuit.measure(0, 0)
        with circuit.box([Twirl(dressing="left")]):
            circuit.measure(1, 0)

        with pytest.raises(
            BuildError, match="Cannot twirl more than one measurement on the same classical bit"
        ):
            pre_build(circuit)
