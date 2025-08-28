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

"""Tests dynamic circuits by simulating them"""

import pytest
from qiskit.circuit import Parameter, QuantumCircuit
from qiskit.circuit.classical import expr

from samplomatic.annotations import Twirl
from samplomatic.builders import pre_build
from samplomatic.exceptions import BuildError, SamplexBuildError

from .utils import sample_simulate_and_compare_counts


class TestWithoutSimulation:
    """Test dynamic circuits without simulation.

    Mostly for error handling."""

    # TODO: Convert this to unit tests.

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
        """Verify that an error is raised if a gate follows a conditional in a right
        dressed box."""
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
        """Verify that an error is raised if a conditional follows a gate in a left
        dressed box."""
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

    def test_twirled_clbit_in_passthroguh_condition_error(self, save_plot):
        """Test that an error is raised if a passthrough conditional depends on a twirled
        classical bit."""
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

    def test_twirled_clregister_in_passthrough_condition_error(self, save_plot):
        """Test that an error is raised if a passthrough conditional depends on a twirled
        classical register."""
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

    def test_twirled_clbit_in_right_condition_error(self, save_plot):
        """Test that an error is raised if a right-box conditional depends on a twirled
        classical bit."""
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

    def test_twirled_clregister_in_right_condition_error(self, save_plot):
        """Test that an error is raised if a right-box conditional depends on a twirled
        classical register."""
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

    def test_twirled_clbit_in_left_condition_error(self, save_plot):
        """Test that an error is raised if a left-box conditional depends on a twirled
        classical bit."""
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

    def test_twirled_clregister_in_left_condition_error(self, save_plot):
        """Test that an error is raised if a left-box conditional depends on a twirled
        classical register."""
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

    def test_twirled_expr_in_left_condition_error(self, save_plot):
        """Test that an error is raised if a left-box conditional depends on a twirled
        classical expression."""
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


class TestWithSimulation:
    """Test dynamic circuits with QiskitAer."""

    def test_non_twirled_conditional(self, save_plot):
        """Test a circuit with a non-twirled conditional."""
        circuit = QuantumCircuit(2, 2)
        with circuit.box([Twirl(dressing="left")]):
            circuit.h(0)
            circuit.noop(1)
        with circuit.box([Twirl(dressing="right")]):
            circuit.noop(0, 1)
        circuit.measure(0, 0)
        with circuit.if_test((circuit.clbits[0], 1)) as _else:
            circuit.sx(1)
        with _else:
            circuit.x(1)
        circuit.measure_all()

        sample_simulate_and_compare_counts(circuit, save_plot)

    def test_non_twirled_parametric_conditional(self, save_plot):
        """Test a circuit with a non-twirled, parameteric conditional."""
        circuit = QuantumCircuit(2, 2)
        p = Parameter("p")
        with circuit.box([Twirl(dressing="left")]):
            circuit.h(0)
            circuit.noop(1)
        with circuit.box([Twirl(dressing="right")]):
            circuit.noop(0, 1)
        circuit.measure(0, 0)
        with circuit.if_test((circuit.clbits[0], 1)) as _else:
            circuit.sx(1)
            circuit.rz(p, 1)
            circuit.rz(2 * p, 1)
            circuit.sx(1)
        with _else:
            circuit.x(1)
            circuit.rx(Parameter("a"), 0)
        circuit.measure_all()

        sample_simulate_and_compare_counts(circuit, save_plot)

    def test_right_dressed_twirled_conditional(self, save_plot):
        """Test a circuit with a conditional in a right-dressed twirl box."""
        circuit = QuantumCircuit(3, 2)
        circuit.h(0)
        circuit.measure(0, 0)

        with circuit.box([Twirl(dressing="left")]):
            circuit.noop(0, 1, 2)
        with circuit.box([Twirl(dressing="right")]):
            circuit.cx(0, 1)
            with circuit.if_test((circuit.clbits[0], 1)) as _else:
                circuit.cx(0, 1)
                circuit.x(0)
            with _else:
                circuit.cx(1, 0)
                circuit.sx(0)
            circuit.x(2)
        circuit.h(1)
        circuit.measure_all()

        sample_simulate_and_compare_counts(circuit, save_plot)

    def test_right_dressed_twirled_conditional_no_else(self, save_plot):
        """Test a conditional without else clause in a right-dressed twirl box."""
        circuit = QuantumCircuit(3, 2)
        circuit.h(0)
        circuit.measure(0, 0)

        with circuit.box([Twirl(dressing="left")]):
            circuit.noop(0, 1, 2)
        with circuit.box([Twirl(dressing="right")]):
            circuit.cx(0, 1)
            with circuit.if_test((circuit.clbits[0], 1)):
                circuit.cx(0, 1)
                circuit.x(0)
            circuit.x(2)
        circuit.h(1)
        circuit.measure_all()

        sample_simulate_and_compare_counts(circuit, save_plot)

    def test_right_dressed_parametric_twirled_conditional(self, save_plot):
        """Test a circuit with a parametric conditional in a right-dressed twirl box."""
        circuit = QuantumCircuit(3, 1)
        p = Parameter("p")
        circuit.h(0)
        circuit.measure(0, 0)

        with circuit.box([Twirl(dressing="left")]):
            circuit.noop(0, 1, 2)
        with circuit.box([Twirl(dressing="right")]):
            circuit.cx(0, 1)
            with circuit.if_test((circuit.clbits[0], 1)) as _else:
                circuit.cx(0, 1)
                circuit.x(0)
                circuit.rx(p, 0)
            with _else:
                circuit.cx(1, 0)
                circuit.sx(0)
                circuit.rx(2 * p, 1)
            circuit.x(2)
        circuit.h(1)
        circuit.measure_all()

        sample_simulate_and_compare_counts(circuit, save_plot)

    def test_left_dressed_twirled_conditional(self, save_plot):
        """Test a circuit with a conditional in a left-dressed twirl box."""
        circuit = QuantumCircuit(3, 2)
        circuit.h(0)
        circuit.measure(0, 0)

        with circuit.box([Twirl(dressing="left")]):
            with circuit.if_test((circuit.clbits[0], 1)) as _else:
                circuit.x(0)
                circuit.cx(0, 1)
            with _else:
                circuit.sx(0)
                circuit.cx(1, 0)
            circuit.x(2)
            circuit.cx(0, 1)
        with circuit.box([Twirl(dressing="right")]):
            circuit.h(1)
            circuit.noop(0, 2)

        circuit.measure_all()

        sample_simulate_and_compare_counts(circuit, save_plot)

    def test_left_dressed_twirled_conditional_no_else(self, save_plot):
        """Test a conditional without else clause in a left-dressed twirl box."""
        circuit = QuantumCircuit(3, 2)
        circuit.h(0)
        circuit.measure(0, 0)

        with circuit.box([Twirl(dressing="left")]):
            with circuit.if_test((circuit.clbits[0], 1)):
                circuit.x(0)
                circuit.cx(0, 1)
            circuit.x(2)
            circuit.cx(0, 1)
        with circuit.box([Twirl(dressing="right")]):
            circuit.h(1)
            circuit.noop(0, 2)

        circuit.measure_all()

        sample_simulate_and_compare_counts(circuit, save_plot)

    def test_left_dressed_parametric_twirled_conditional(self, save_plot):
        """Test a circuit with a parametric conditional in a left-dressed twirl box."""
        circuit = QuantumCircuit(3, 1)
        p = Parameter("p")
        circuit.h(0)
        circuit.measure(0, 0)

        with circuit.box([Twirl(dressing="left")]):
            with circuit.if_test((circuit.clbits[0], 1)) as _else:
                circuit.x(0)
                circuit.rx(p, 1)
                circuit.cx(0, 1)
            with _else:
                circuit.sx(0)
                circuit.rx(2 * p, 0)
                circuit.cx(1, 0)
            circuit.x(2)
            circuit.cx(0, 1)
        with circuit.box([Twirl(dressing="right")]):
            circuit.h(1)
            circuit.noop(0, 2)

        circuit.measure_all()

        sample_simulate_and_compare_counts(circuit, save_plot)
