# This code is a Qiskit project.
#
# (C) Copyright IBM 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""RandomizedRzRxSynth"""

import numpy as np
from qiskit.circuit import CircuitInstruction, Parameter, Qubit
from qiskit.circuit.library import RXGate, RZGate

from ..exceptions import SynthError
from ..virtual_registers import PauliRegister, U2Register, VirtualType
from .synth import Synth

TOL = 1e-15


class RandomizedRzRxSynth(Synth[Qubit, Parameter, CircuitInstruction]):
    """Synthesizes single-qubit gates into rz-rx-rz-rx-rz with randomized rx angles.

    Uses a per-sample random rx angle to probe angle-dependent noise during
    randomized compiling, producing a noise model more representative of
    circuits with varied rx angles.
    """

    num_params: int = 5
    compatible_register_types = frozenset({VirtualType.PAULI, VirtualType.U2})

    def make_template(self, qubits, params):
        try:
            yield CircuitInstruction(RZGate(next(params)), qubits)
            yield CircuitInstruction(RXGate(next(params)), qubits)
            yield CircuitInstruction(RZGate(next(params)), qubits)
            yield CircuitInstruction(RXGate(next(params)), qubits)
            yield CircuitInstruction(RZGate(next(params)), qubits)
        except StopIteration as ex:
            raise SynthError(f"Not enough parameters provided to {self}.") from ex

    def generate_template_values(self, register, rng=None):
        if rng is None:
            raise SynthError(f"{self} requires an rng to generate template values.")

        if (register_type := type(register)) is PauliRegister:
            return self._generate_pauli_values(register, rng)
        if register_type is U2Register:
            return self._generate_u2_values(register, rng)

        raise SynthError(f"Register of type '{register_type}' is not understood by {self}.")

    def _generate_pauli_values(self, register, rng):
        gates = register.virtual_gates
        shape = gates.shape + (5,)
        values = np.empty(shape)

        delta = rng.uniform(0, np.pi, size=gates.shape)

        x_bit = gates >= 2
        z_bit = (gates & 1).astype(bool)

        # p3 (second Rx in circuit = δ₁ in matrix order)
        values[..., 3] = delta
        # p1 (first Rx in circuit = δ₂ in matrix order)
        values[..., 1] = np.where(x_bit, np.pi - delta, delta)
        # p2 (middle Rz)
        values[..., 2] = np.where(x_bit, 0.0, np.pi)
        # p4 (last Rz in circuit = leftmost in matrix = a)
        values[..., 4] = np.where(
            x_bit, np.where(z_bit, np.pi / 2, 0.0), np.where(z_bit, np.pi / 2, -np.pi / 2)
        )
        # p0 (first Rz in circuit = rightmost in matrix = c)
        values[..., 0] = np.where(x_bit, np.where(z_bit, -np.pi / 2, 0.0), -np.pi / 2)

        return values

    def _generate_u2_values(self, register, rng):
        gates = register.virtual_gates

        phase = (gates[..., 0, 0] * gates[..., 1, 1] - gates[..., 0, 1] * gates[..., 1, 0]) ** -0.5

        phi_plus_lambda = np.angle(phase * gates[..., 1, 1])
        phi_minus_lambda = np.angle(phase * gates[..., 1, 0])
        phi = phi_plus_lambda + phi_minus_lambda + np.pi / 2
        theta = 2 * np.arctan2(np.abs(gates[..., 1, 0]), np.abs(gates[..., 0, 0]))
        lam = phi_plus_lambda - phi_minus_lambda - np.pi / 2

        values = np.empty(gates.shape[:2] + (5,))

        # Per-sample branching: symmetric for θ ≤ π/2, complementary for θ > π/2
        half_theta = theta / 2
        sym_mask = theta <= np.pi / 2

        # --- Symmetric regime (δ₁ = δ₂ = δ): valid δ ∈ [θ/2, π - θ/2] ---
        if np.any(sym_mask):
            low = half_theta[sym_mask]
            high = np.pi - low
            delta_sym = rng.uniform(size=low.shape) * (high - low) + low

            sin_delta = np.sin(delta_sym)
            sin_ht = np.sin(low)
            cos_delta = np.cos(delta_sym)

            # b = 2·arccos(sin(θ/2) / sin(δ))
            ratio = sin_ht / sin_delta
            np.clip(ratio, -1, 1, out=ratio)
            b = 2 * np.arccos(ratio)

            # α = arctan2(√(sin²δ - sin²(θ/2)), cosδ·sin(θ/2))
            residual = np.sqrt(np.maximum(sin_delta**2 - sin_ht**2, 0.0))
            alpha = np.arctan2(residual, cos_delta * sin_ht)

            values[sym_mask, 0] = lam[sym_mask] - alpha
            values[sym_mask, 1] = delta_sym
            values[sym_mask, 2] = b
            values[sym_mask, 3] = delta_sym
            values[sym_mask, 4] = phi[sym_mask] - alpha

        # --- Complementary regime (δ₁ + δ₂ = π): valid δ₁ ∈ [(π-θ)/2, (π+θ)/2] ---
        comp_mask = ~sym_mask
        if np.any(comp_mask):
            ht = half_theta[comp_mask]
            low = (np.pi - theta[comp_mask]) / 2
            high = (np.pi + theta[comp_mask]) / 2
            delta_comp = rng.uniform(size=low.shape) * (high - low) + low

            sin_delta = np.sin(delta_comp)
            cos_ht = np.cos(ht)
            cos_delta = np.cos(delta_comp)

            # b = 2·arcsin(cos(θ/2) / sin(δ₁))
            ratio = cos_ht / sin_delta
            np.clip(ratio, -1, 1, out=ratio)
            b = 2 * np.arcsin(ratio)

            # β = arctan2(cosδ·cos(θ/2), √(sin²δ - cos²(θ/2)))
            residual = np.sqrt(np.maximum(sin_delta**2 - cos_ht**2, 0.0))
            beta = np.arctan2(cos_delta * cos_ht, residual)

            values[comp_mask, 0] = lam[comp_mask] - np.pi / 2 + beta
            values[comp_mask, 1] = np.pi - delta_comp
            values[comp_mask, 2] = b
            values[comp_mask, 3] = delta_comp
            values[comp_mask, 4] = phi[comp_mask] - np.pi / 2 - beta

        # restrict all angles to (-pi, pi]
        return -np.remainder(-values + np.pi, 2 * np.pi) + np.pi
