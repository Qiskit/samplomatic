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

from __future__ import annotations

import enum
from dataclasses import dataclass, field

import numpy as np

from ..aliases import (
    CircuitInstruction,
    ClbitIndex,
    Parameter,
    ParamIndices,
    ParamSpec,
    Qubit,
    StrRef,
)
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
    """A unique identifier of the basis transformation."""

    noise_ref: StrRef = ""
    """A unique identifier of the noise map."""

    noise_modifier_ref: StrRef = ""
    """A unique identifier of modifiers for the noise map."""


@dataclass
class CollectionSpec:
    """Specification for a collection event on some qubits within a box."""

    qubits: QubitPartition
    """Which source subsystems to collect on."""

    dressing: DressingMode | None = None
    """Which side of the box to collect on."""

    synth: Synth[Qubit, Parameter, CircuitInstruction] | None = None
    """How to synthesize collection gates."""


@dataclass
class InstructionSpec:
    """Specification of an instruction."""

    params: ParamSpec = field(default_factory=list)
    """A list of tuples of parameter indices in the template circuit and corresponding expressions.

    An index of ``None`` indicates that the expression is not added to the template."""

    param_idxs: ParamIndices = field(default_factory=lambda: EMPTY_IDXS)
    """A matrix of parameter indices specifing virtual gate synthesis locations in the template.

    The first axis is over subsystems, the second over parameters in a synthesizer decomposition.
    """

    mode: InstructionMode = InstructionMode.NONE
    """The mode of an added instruction."""

    clbit_idxs: list[ClbitIndex] = field(default_factory=list)
    """The mode of an added instruction."""

    if_else: tuple[list[InstructionSpec], ParamIndices, list[InstructionSpec], ParamIndices] = (
        field(default_factory=lambda: ([], EMPTY_IDXS, [], EMPTY_IDXS))
    )
    """The specs for an `IfElseOp`.

    Each branch of the operation is represented by two fields: a list of `InstructionSpec` for
    the branch's instructions, followed by `ParamIndices` for the collectors of the branch. The
    true branch is first in the tuple, and the else branch is second."""
