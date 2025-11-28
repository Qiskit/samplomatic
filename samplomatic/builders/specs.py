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

"""High-level node specifications"""

import enum
from dataclasses import dataclass

import numpy as np

from ..aliases import CircuitInstruction, Parameter, Qubit, StrRef
from ..annotations import DressingMode, VirtualType
from ..partition import QubitPartition
from ..synths import Synth

EMPTY_IDXS = np.empty((0, 0), dtype=np.intp)
EMPTY_IDXS.setflags(write=False)


class InstructionMode(enum.Enum):
    """Action mode of an instruction from the base circuit."""

    NONE = 0
    """The instruction is not a gate and this mode is not applicable."""

    PROPAGATE = 1
    """The instruction is a gate and was added to the base circuit.

    Propagation needs to mutate virtual registers according to :math:`V \\mapsto GVG^\\dagger`
    or :math:`V \\mapsto G^\\dagger VG` depending on travel direction.
    """

    MULTIPLY = 2
    """The instruction is a gate and was not added to the base circuit.

    The expectation is that this gate will be folded into collections. Propagation needs to mutate
    virtual registers according to :math:`V \\mapsto GV` or :math:`V \\mapsto VG` depending on
    travel direction.
    """


@dataclass
class EmissionSpec:
    """Specification for an emission event on some qubits within a box."""

    qubits: QubitPartition
    """Which source subsystems to emit to."""

    dressing: DressingMode | None = None
    """Which side of the box to emit on."""

    twirl_register_type: VirtualType | None = None
    """What type of virtual gates to emit for twirling."""

    basis_register_type: VirtualType | None = None
    """What type of virtual gates to emit for basis changes."""

    basis_ref: StrRef = ""
    """A unique identifier of the basis change."""

    noise_ref: StrRef = ""
    """A unique identifier of the Pauli Lindblad map to use for noise injection."""

    noise_modifier_ref: StrRef = ""
    """A unique identifier for modifiers to apply to the Pauli Lindblad map."""


@dataclass
class CollectionSpec:
    """Specification for a collection event on some qubits within a box."""

    qubits: QubitPartition
    """Which source subsystems to collect on."""

    dressing: DressingMode | None = None
    """Which side of the box to collect on."""

    synth: Synth[Qubit, Parameter, CircuitInstruction] | None = None
    """How to synthesize collection gates."""
