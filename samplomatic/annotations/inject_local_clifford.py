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

"""InjectLocalClifford"""

from qiskit.circuit import Annotation

from ..aliases import StrRef
from .decomposition_mode import DecompositionLiteral, DecompositionMode
from .dressing_mode import DressingLiteral, DressingMode


class InjectLocalClifford(Annotation):
    """Directive to inject local Cliffords.

    The resulting :class:`~.Samplex` built from a circuit with a box with this annotation has
    a tensor input with name ``local_cliffords.ref`` and shape ``'(len(box_instruction.qubits),)'``.
    The tensor is indexed in physical qubit order, in other words, the order of the qubits in the
    outer-most circuit, restricted to those used by the box.

    Args:
        ref: A unique identifier of the Cliffords.
        decomposition: How to decompose the Cliffords.
        dressing: Which side of the box to attach the dressing instructions.
    """

    namespace = "samplomatic.inject_local_clifford"

    __slots__ = ("decomposition", "dressing", "ref")

    def __init__(
        self,
        ref: StrRef,
        decomposition: DecompositionLiteral = DecompositionMode.RZSX,
        dressing: DressingLiteral = DressingMode.LEFT,
    ):
        self.decomposition = DecompositionMode(decomposition)
        self.dressing = DressingMode(dressing)
        self.ref = ref

    def __eq__(self, other):
        return (
            isinstance(other, InjectLocalClifford)
            and self.decomposition == other.decomposition
            and self.dressing == other.dressing
            and self.ref == other.ref
        )

    def __hash__(self):
        return hash((self.decomposition, self.dressing, self.ref))

    def __repr__(self):
        return (
            f"{type(self).__name__}(ref='{self.ref}', decomposition="
            f"'{self.decomposition.name.lower()}', dressing='{self.dressing.name.lower()}')"
        )
