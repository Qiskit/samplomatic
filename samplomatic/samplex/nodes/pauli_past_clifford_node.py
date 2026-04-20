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

"""PauliPastCliffordNode"""

from collections.abc import Sequence

import numpy as np

from ...aliases import OperationName, RegisterName, SubsystemIndex
from ...exceptions import SamplexBuildError
from ...virtual_registers import VirtualType
from .evaluation_node import EvaluationNode

# The projective Pauli conjugation action of a 1Q Clifford is a permutation of {Z, X, Y}
# (I is always fixed), i.e. an element of S_3. The 5 non-trivial elements are defined
# below as named constants (the identity corresponds to PAULI_PAST_CLIFFORD_INVARIANTS).
# Pauli encoding: I=0, Z=1, X=2, Y=3.

# Order-2 elements (transpositions):
_PAULI_SWAP_ZX = np.array([[0], [2], [1], [3]], dtype=np.intp)  # Z↔X  (e.g. h)
_PAULI_SWAP_XY = np.array([[0], [1], [3], [2]], dtype=np.intp)  # X↔Y  (canonical: s)
_PAULI_SWAP_ZY = np.array([[0], [3], [2], [1]], dtype=np.intp)  # Z↔Y  (canonical: sx)

# Order-3 elements (3-cycles). Names use circuit-application order (left = applied first):
_PAULI_CYCLE_ZXY = np.array([[0], [2], [3], [1]], dtype=np.intp)  # Z→X→Y→Z  (e.g. s@h)
_PAULI_CYCLE_ZYX = np.array([[0], [3], [1], [2]], dtype=np.intp)  # Z→Y→X→Z  (e.g. h@s)

PAULI_PAST_CLIFFORD_CANONICAL_NAMES: dict[str, str] = {
    "sdg": "s",
    "sxdg": "sx",
}
"""Mapping to canonical gate names for Pauli propagation.

Gates with the same projective Pauli conjugation action are canonicalized to a single
representative name so that :class:`~.PauliPastCliffordNode` instances acting identically
share the same key and can be merged during optimization.
"""

PAULI_PAST_CLIFFORD_LOOKUP_TABLES = {
    "h": _PAULI_SWAP_ZX,
    "s": _PAULI_SWAP_XY,
    "sx": _PAULI_SWAP_ZY,
    "sh": _PAULI_CYCLE_ZXY,
    "hs": _PAULI_CYCLE_ZYX,
    # Two-qubit gates
    "cx": np.array(
        [
            [[0, 0], [1, 1], [0, 2], [1, 3]],
            [[1, 0], [0, 1], [1, 2], [0, 3]],
            [[2, 2], [3, 3], [2, 0], [3, 1]],
            [[3, 2], [2, 3], [3, 0], [2, 1]],
        ],
        dtype=np.intp,
    ),
    "cz": np.array(
        [
            [[0, 0], [0, 1], [1, 2], [1, 3]],
            [[1, 0], [1, 1], [0, 2], [0, 3]],
            [[2, 1], [2, 0], [3, 3], [3, 2]],
            [[3, 1], [3, 0], [2, 3], [2, 2]],
        ],
        dtype=np.intp,
    ),
    "ecr": np.array(
        [
            [[0, 0], [1, 3], [0, 2], [1, 1]],
            [[1, 0], [0, 3], [1, 2], [0, 1]],
            [[3, 2], [2, 1], [3, 0], [2, 3]],
            [[2, 2], [3, 1], [2, 0], [3, 3]],
        ],
        dtype=np.intp,
    ),
}
"""Lookup tables for computing the conjugation of Pauli operators by Clifford gates.

Single-qubit Pauli operators are indexed as in :class:`~.PauliRegister`\\s. Computing the
conjugation of a Pauli by a Clifford can be done via slicing. For example,
``PAULI_PAST_CLIFFORD_LOOKUP_TABLES["h"][i]`` gives the conjugation of a Pauli ``i`` by
an H gate, while ``PAULI_PAST_CLIFFORD_LOOKUP_TABLES["cx"][i, j]`` gives that of Paulis
``i`` and ``j`` by CX.
"""

PAULI_PAST_CLIFFORD_INVARIANTS = {"x", "z", "y", "id"}
"""Set of gates which a Pauli is invariant (up to a sign) under conjugation with."""


class PauliPastCliffordNode(EvaluationNode):
    """A node that propagates a Pauli register past a Clifford gate.

    Args:
        op_name: The name of the Clifford gate.
        register_name: The name of the Pauli register to propagate.
        subsystem_idxs: The subsystems in the register. The expected format is
            that of a collection of subsystems of the same size, i.e., that
            of a 2D array where the left-most axes is over subsystems and
            the right-most axes is over qubits.
    """

    def __init__(
        self,
        op_name: OperationName,
        register_name: RegisterName,
        subsystem_idxs: Sequence[Sequence[SubsystemIndex]],
    ):
        try:
            self._lookup_table = PAULI_PAST_CLIFFORD_LOOKUP_TABLES[op_name]
        except KeyError:
            supported_gates = list(PAULI_PAST_CLIFFORD_LOOKUP_TABLES)
            raise SamplexBuildError(f"Expected one of {supported_gates}, found {op_name}.")

        self._op_name = op_name
        self._subsystem_idxs = np.asarray(subsystem_idxs, dtype=np.intp)
        self._register_name = register_name

    @property
    def outgoing_register_type(self) -> VirtualType:
        return VirtualType.PAULI

    def evaluate(self, registers, *_):
        reg = registers[self._register_name]
        subsys = self._subsystem_idxs

        paulis_in = reg.virtual_gates[subsys]
        paulis_out = self._lookup_table[tuple(paulis_in[:, i] for i in range(subsys.shape[-1]))]
        reg.virtual_gates[subsys] = np.transpose(paulis_out, (0, 2, 1))

    def reads_from(self):
        return {
            self._register_name: (
                set(s for tup in self._subsystem_idxs for s in tup),
                VirtualType.PAULI,
            )
        }

    def writes_to(self):
        return {
            self._register_name: (
                set(s for tup in self._subsystem_idxs for s in tup),
                VirtualType.PAULI,
            )
        }

    def __eq__(self, other):
        return (
            isinstance(other, PauliPastCliffordNode)
            and self._op_name == other._op_name
            and np.array_equal(self._subsystem_idxs, other._subsystem_idxs)
            and self._register_name == other._register_name
        )

    def get_style(self):
        return (
            super()
            .get_style()
            .append_data("Operation", repr(self._op_name))
            .append_data("Register Name", repr(self._register_name))
            .append_list_data("Subsystem Indices", self._subsystem_idxs.tolist())
        )
