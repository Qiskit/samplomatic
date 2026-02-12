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

"""Twirl"""

from qiskit.circuit import Annotation

from ..utils.deprecation import deprecate_arg
from .decomposition_mode import DecompositionLiteral, DecompositionMode
from .dressing_mode import DressingLiteral, DressingMode
from .group_mode import GroupLiteral, GroupMode


class Twirl(Annotation):
    """Directive to twirl the contents of a ``box`` instruction.

    Args:
        group: Which group to twirl with.
        dressing: Which side of the box to attach the dressing instructions.
        decomposition: How to decompose single-qubit gates.
    """

    namespace = "samplomatic.twirl"

    __slots__ = ("group", "dressing", "decomposition")

    @deprecate_arg(
        "group",
        since="0.17.0",
        # we avoid isinstance in the predicate in order to avoid a dependency on ..virtual_registers
        predicate=lambda group: type(group).__name__.startswith("VirtualType"),
        deprecation_description="Providing a VirtualType enum as the 'group' argument of Twirl.",
        additional_msg="Instead, use a string literal or the GroupMode enum.",
    )
    def __init__(
        self,
        group: GroupLiteral = GroupMode.PAULI,
        dressing: DressingLiteral = DressingMode.LEFT,
        decomposition: DecompositionLiteral = DecompositionMode.RZSX,
    ):
        self.group = GroupMode(group)
        self.dressing = DressingMode(dressing)
        self.decomposition = DecompositionMode(decomposition)

    def __eq__(self, other):
        return (
            isinstance(other, Twirl)
            and self.group == other.group
            and self.dressing == other.dressing
            and self.decomposition == other.decomposition
        )

    def __hash__(self):
        return hash((self.group, self.dressing, self.decomposition))

    def __repr__(self):
        return (
            f"{type(self).__name__}(group='{self.group.name.lower()}', dressing="
            f"'{self.dressing.name.lower()}', decomposition='{self.decomposition.name.lower()}')"
        )
