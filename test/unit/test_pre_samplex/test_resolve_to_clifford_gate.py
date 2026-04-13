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

"""Tests for _resolve_to_clifford_gate."""

import numpy as np
import pytest
from qiskit.circuit import Parameter
from qiskit.circuit.library import (
    HGate,
    IGate,
    PhaseGate,
    RXGate,
    RZGate,
    SGate,
    SXGate,
    TGate,
    XGate,
    ZGate,
)

from samplomatic.pre_samplex.pre_samplex import _resolve_to_clifford_gate


class TestResolveToCliffordGate:
    """Tests for the _resolve_to_clifford_gate helper."""

    @pytest.mark.parametrize(
        "gate, expected_type",
        [
            # rz at Clifford angles (3π/2 canonicalized to SGate, same Pauli action as π/2)
            (RZGate(0.0), IGate),
            (RZGate(np.pi / 2), SGate),
            (RZGate(np.pi), ZGate),
            (RZGate(3 * np.pi / 2), SGate),
            # rx at Clifford angles (3π/2 canonicalized to SXGate, same Pauli action as π/2)
            (RXGate(0.0), IGate),
            (RXGate(np.pi / 2), SXGate),
            (RXGate(np.pi), XGate),
            (RXGate(3 * np.pi / 2), SXGate),
            # p (PhaseGate) at Clifford angles — same Pauli action as rz
            (PhaseGate(0.0), IGate),
            (PhaseGate(np.pi / 2), SGate),
            (PhaseGate(np.pi), ZGate),
            (PhaseGate(3 * np.pi / 2), SGate),
        ],
    )
    def test_resolves_clifford_angles(self, gate, expected_type):
        """Concrete Clifford-angle rotation gates resolve to the named gate type."""
        result = _resolve_to_clifford_gate(gate)
        assert isinstance(result, expected_type)

    @pytest.mark.parametrize(
        "gate",
        [
            RZGate(np.pi / 4),  # T angle — not a Clifford angle
            RZGate(np.pi / 3),
            RXGate(np.pi / 4),
            RXGate(1.23),
        ],
    )
    def test_non_clifford_angles_return_none(self, gate):
        """Non-Clifford angles return None."""
        assert _resolve_to_clifford_gate(gate) is None

    @pytest.mark.parametrize(
        "gate",
        [
            RZGate(Parameter("theta")),
            RXGate(Parameter("phi")),
        ],
    )
    def test_symbolic_params_return_none(self, gate):
        """Gates with unbound symbolic parameters return None."""
        assert _resolve_to_clifford_gate(gate) is None

    def test_unrecognized_gate_returns_none(self):
        """Gate types other than rz, p, rx return None."""
        assert _resolve_to_clifford_gate(HGate()) is None
        assert _resolve_to_clifford_gate(TGate()) is None
        assert _resolve_to_clifford_gate(XGate()) is None

    @pytest.mark.parametrize(
        "gate, expected_type",
        [
            # Angles > 2π normalize correctly
            (RZGate(2 * np.pi + np.pi / 2), SGate),
            (RXGate(4 * np.pi + np.pi), XGate),
            # Negative angles normalize correctly (Python % returns positive)
            (RZGate(-np.pi / 2), SGate),  # -π/2 mod 2π = 3π/2, canonicalized to s
            (RXGate(-np.pi / 2), SXGate),  # -π/2 mod 2π = 3π/2, canonicalized to sx
        ],
    )
    def test_angle_normalization(self, gate, expected_type):
        """Angles outside [0, 2π) are normalized correctly."""
        result = _resolve_to_clifford_gate(gate)
        assert isinstance(result, expected_type)
