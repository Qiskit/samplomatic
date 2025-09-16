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

"""Tests dynamic circuits by simulating them."""

from qiskit.circuit import Parameter, QuantumCircuit

from samplomatic.annotations import Twirl

from .utils import sample_simulate_and_compare_counts


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
