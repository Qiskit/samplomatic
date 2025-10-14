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

"""Tests measurement twirling by simulating the circuits"""

import numpy as np
import pytest
from qiskit.circuit import ClassicalRegister, QuantumCircuit, QuantumRegister

from samplomatic.annotations import Twirl
from samplomatic.builders import pre_build

from .utils import sample_simulate_and_compare_counts


class TestWithoutSimulation:
    """Test measurement twirling without simulation"""

    def test_non_twirled_measurements(self):
        """Verify that non twirled measurements don't get a correction"""
        circuit = QuantumCircuit(2, 3)
        circuit.x(0)
        with circuit.box([Twirl(dressing="left")]):
            circuit.measure(0, 0)
        circuit.measure(1, 2)

        _, samplex_state = pre_build(circuit)
        samplex = samplex_state.finalize()
        samplex.finalize()

        samplex_input = samplex.inputs()
        samplex_output = samplex.sample(samplex_input, num_randomizations=20)
        measurement_flips = samplex_output["measurement_flips.c"]
        assert not np.any(measurement_flips[:, 1:3])


class TestWithSimulation:
    """Test measurement twirling with a simulator."""

    def test_measure_all(self, save_plot):
        circuit = QuantumCircuit(3)
        circuit.x(0)
        circuit.h(1)
        with circuit.box([Twirl(dressing="left")]):
            circuit.measure_all()
        sample_simulate_and_compare_counts(circuit, save_plot)

    def test_gates_and_measure_all(self, save_plot):
        circuit = QuantumCircuit(3)
        with circuit.box([Twirl(dressing="left")]):
            circuit.x(0)
            circuit.h(1)
            circuit.cx(0, 1)
            circuit.measure_all()
        sample_simulate_and_compare_counts(circuit, save_plot)

    def test_separate_measures(self, save_plot):
        """Test separate measurement instructions, with non-standard cbit associations"""
        circuit = QuantumCircuit(QuantumRegister(size=3), ClassicalRegister(name="meas", size=3))
        circuit.x(0)
        circuit.h(1)
        with circuit.box([Twirl(dressing="left")]):
            circuit.measure(0, 2)
            circuit.measure(1, 0)
            circuit.measure(2, 1)

        sample_simulate_and_compare_counts(circuit, save_plot)

    @pytest.mark.skip(reason="QiskitAer bug #2367")
    def test_separate_measure_boxes(self, save_plot):
        """Test separate measurement boxes, with non-standard cbit associations"""
        circuit = QuantumCircuit(QuantumRegister(size=3), ClassicalRegister(name="meas", size=3))
        circuit.x(0)
        circuit.h(1)
        with circuit.box([Twirl(dressing="left")]):
            circuit.measure(0, 2)
        with circuit.box([Twirl(dressing="left")]):
            circuit.measure(1, 0)
        with circuit.box([Twirl(dressing="left")]):
            circuit.measure(2, 1)

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

    def test_mid_circuit_measurements(self, save_plot):
        """Test separate measurement boxes, with repeated twirled measurements on the same qubit"""
        circuit = QuantumCircuit(QuantumRegister(size=1), ClassicalRegister(name="meas", size=3))
        circuit.x(0)
        circuit.h(0)
        with circuit.box([Twirl(dressing="left")]):
            circuit.measure(0, 0)
        with circuit.box([Twirl(dressing="left")]):
            circuit.measure(0, 2)

        sample_simulate_and_compare_counts(circuit, save_plot)

    @pytest.mark.skip(
        reason="Mid-circuit measurements followed by non twirled measurements are not supported yet"
    )
    def test_mid_circuit_measurements_followed_by_non_twirled_measurement(self, save_plot):
        """Test a twirled measurement followed by a non twirled measurement on the same qubit"""
        circuit = QuantumCircuit(1, 3)
        circuit.x(0)
        circuit.h(0)
        with circuit.box([Twirl(dressing="left")]):
            circuit.measure(0, 0)
        with circuit.box([Twirl(dressing="right")]):
            circuit.noop(0)
        circuit.measure_all()

        sample_simulate_and_compare_counts(circuit, save_plot)

    def test_partially_twirled_measurements(self, save_plot):
        """Verify that twirling only some of the measurements works"""
        circuit = QuantumCircuit(QuantumRegister(size=2), ClassicalRegister(name="meas", size=3))
        circuit.x(0)
        with circuit.box([Twirl(dressing="left")]):
            circuit.measure(0, 0)
        circuit.measure(1, 2)

        sample_simulate_and_compare_counts(circuit, save_plot)
