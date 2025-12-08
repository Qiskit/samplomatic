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

"""CorpseSynth"""

import numpy as np
from qiskit.circuit import CircuitInstruction, Parameter, Qubit
from qiskit.circuit.library import RXGate, RZGate, XGate, ZGate

from ..annotations import VirtualType
from ..exceptions import SynthError
from ..virtual_registers import U2Register
from .synth import Synth


class CorpseSynth(Synth[Qubit, Parameter, CircuitInstruction]):
    """Synthesizes arbitrary single-qubit gates with the CORPSE composite pulse."""

    num_params: int = 4
    compatible_register_types = frozenset({VirtualType.U2})

    def make_template(self, qubits, params):
        x = CircuitInstruction(XGate(), qubits)
        z = CircuitInstruction(ZGate(), qubits)
        try:
            yield CircuitInstruction(RZGate(next(params)), qubits)
            # yield x
            yield (theta1 := CircuitInstruction(RXGate(next(params)), qubits))
            # yield x
            yield z
            yield x
            yield CircuitInstruction(RXGate(next(params)), qubits)
            yield z
            yield x
            yield x
            yield theta1
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

            # theta is the desired rx angle
            theta_over_two = np.arctan2(np.abs(gates[..., 1, 0]), np.abs(gates[..., 0, 0]))
            asin_sin = np.arcsin(np.sin(theta_over_two) / 2)

            # in CORPSE, we have theta1=theta3, but with 2*pi added to theta1. however, we handle
            # the extra 2*pi by inserting static X gates, so the same parameter value is used for
            # them here. similarly, we insert one of the 2 pi's added to theta2 via a static X gate,
            # hence we only add pi to -2*asin_sin.
            theta13 = theta_over_two - asin_sin
            theta2 = np.pi - 2 * asin_sin

            values = np.empty(gates.shape[:2] + (4,))
            values[..., 3] = phi_plus_lambda + phi_minus_lambda + np.pi / 2
            values[..., 2] = theta2
            values[..., 1] = theta13
            values[..., 0] = phi_plus_lambda - phi_minus_lambda - np.pi / 2

            # restrict all angles to (-pi, pi]
            return -np.remainder(-values + np.pi, 2 * np.pi) + np.pi

        raise SynthError(f"Register of type '{register_type}' is not understood by {self}.")
