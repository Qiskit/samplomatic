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

"""RzSxSynth"""

import numpy as np
from qiskit.circuit import CircuitInstruction, Parameter, Qubit
from qiskit.circuit.library import RZGate, SXGate

from ..annotations import VirtualType
from ..exceptions import SynthError
from ..virtual_registers import U2Register
from .synth import Synth


class RzSxSynth(Synth[Qubit, Parameter, CircuitInstruction]):
    """Synthesizes arbitrary single-qubit gates into rz-sx-rz-sx-rz."""

    num_params: int = 3
    compatible_register_types = frozenset({VirtualType.U2})

    def make_template(self, qubits, params):
        try:
            yield CircuitInstruction(RZGate(next(params)), qubits)
            yield CircuitInstruction(SXGate(), qubits)
            yield CircuitInstruction(RZGate(next(params)), qubits)
            yield CircuitInstruction(SXGate(), qubits)
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
            values[..., 2] = phi_plus_lambda + phi_minus_lambda
            values[..., 1] = np.pi - 2 * np.arctan2(
                np.abs(gates[..., 1, 0]), np.abs(gates[..., 0, 0])
            )
            values[..., 0] = phi_plus_lambda - phi_minus_lambda - np.pi

            # restrict all angles to (-pi, pi]
            return -np.remainder(-values + np.pi, 2 * np.pi) + np.pi

        raise SynthError(f"Register of type '{register_type.TYPE}' is not understood by {self}.")
