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

"""RzRxSynth"""

import numpy as np
from qiskit.circuit import CircuitInstruction, Parameter, Qubit
from qiskit.circuit.library import RXGate, RZGate

from ..exceptions import SynthError
from ..virtual_registers import U2Register, VirtualType
from .synth import Synth

TOL = 1e-15


class RzRxSynth(Synth[Qubit, Parameter, CircuitInstruction]):
    """Synthesizes arbitrary single-qubit gates into rz-rx-rz."""

    num_params: int = 3
    compatible_register_types = frozenset({VirtualType.U2})

    def make_template(self, qubits, params):
        try:
            yield CircuitInstruction(RZGate(next(params)), qubits)
            yield CircuitInstruction(RXGate(next(params)), qubits)
            yield CircuitInstruction(RZGate(next(params)), qubits)
        except StopIteration as ex:
            raise SynthError(f"Not enough parameters provided to {self}.") from ex

    def generate_template_values(self, register):
        if (register_type := type(register)) is U2Register:
            gates = register.virtual_gates

            phase = (
                gates[..., 0, 0] * gates[..., 1, 1] - gates[..., 0, 1] * gates[..., 1, 0]
            ) ** -0.5

            phi_plus_lambda = np.angle(phase * gates[..., 1, 1])
            phi_minus_lambda = np.angle(phase * gates[..., 1, 0])
            values = np.empty(gates.shape[:2] + (3,))
            values[..., 2] = phi_plus_lambda + phi_minus_lambda + np.pi / 2
            values[..., 1] = 2 * np.arctan2(np.abs(gates[..., 1, 0]), np.abs(gates[..., 0, 0]))
            values[..., 0] = phi_plus_lambda - phi_minus_lambda - np.pi / 2

            # if the gate is an RZ rotation we can unify the phases
            center = np.remainder(values[..., 1], 2 * np.pi)
            if np.any(mask := (center < TOL)):
                values[mask, 0] += values[mask, 2]
                values[mask, 2] = 0

            # if the gate is a pi-pulse  we can also unify the phases
            if np.any(mask := (np.abs(center - np.pi) < TOL)):
                values[mask, 0] -= values[mask, 2]
                values[mask, 2] = 0

            # restrict all angles to (-pi, pi]
            return -np.remainder(-values + np.pi, 2 * np.pi) + np.pi

        raise SynthError(f"Register of type '{register_type}' is not understood by {self}.")
