# This code is a Qiskit project.
#
# (C) Copyright IBM 2025-2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Tests reset twirling by simulating the circuits"""

from qiskit.circuit import ClassicalRegister, QuantumCircuit, QuantumRegister

from samplomatic.annotations import Twirl

from .utils import sample_simulate_and_compare_counts


class TestWithSimulation:
    """Test reset twirling using simulation."""

    def test_reset(self, save_plot):
        circuit = QuantumCircuit(3)
        circuit.h(0)
        circuit.cx(0, 1)
        circuit.cx(1, 2)
        with circuit.box([Twirl(dressing="left")]):
            circuit.reset((0, 1, 2))
            circuit.measure_all()
        sample_simulate_and_compare_counts(circuit, save_plot)

    def test_reset_right(self, save_plot):
        circuit = QuantumCircuit(3)
        circuit.h(0)
        circuit.cx(0, 1)
        circuit.cx(1, 2)
        with circuit.box([Twirl(dressing="left")]):
            circuit.noop(0, 1, 2)
        with circuit.box([Twirl(dressing="right")]):
            circuit.reset((0, 1, 2))
            circuit.measure_all()
        sample_simulate_and_compare_counts(circuit, save_plot)

    def test_gates_and_reset(self, save_plot):
        circuit = QuantumCircuit(3)
        with circuit.box([Twirl(dressing="left")]):
            circuit.h(0)
            circuit.cx(0, 1)
            circuit.cx(1, 2)
            circuit.reset(0)
            circuit.measure_all()
        sample_simulate_and_compare_counts(circuit, save_plot)

    def test_separate_boxes(self, save_plot):
        circuit = QuantumCircuit(QuantumRegister(size=2), ClassicalRegister(name="meas", size=3))

        circuit.h(1)
        circuit.cx(1, 0)
        with circuit.box([Twirl(dressing="left")]):
            circuit.reset(0)
            circuit.measure(0, 2)

        with circuit.box([Twirl(dressing="left")]):
            circuit.measure(1, 0)

        with circuit.box([Twirl(dressing="left")]):
            circuit.reset(1)
            circuit.measure(1, 1)

        sample_simulate_and_compare_counts(circuit, save_plot)

    def test_measure_to_different_registers(self, save_plot):
        """Test separate measurement instructions with several classical registers"""
        creg1 = ClassicalRegister(3, "c1")
        creg2 = ClassicalRegister(3, "c2")
        qreg = QuantumRegister(3, "q1")
        circuit = QuantumCircuit(qreg, creg1, creg2)
        circuit.x(0)
        circuit.h(1)
        with circuit.box([Twirl(dressing="left")]):
            circuit.measure(0, creg1[1])
            circuit.measure(1, creg1[2])
            circuit.measure(2, creg2[1])

        sample_simulate_and_compare_counts(circuit, save_plot)
