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

"""InjectNoise"""

from qiskit.circuit import Annotation

from ..aliases import StrRef


class InjectNoise(Annotation):
    """Directive to inject noise into a ``box`` instruction.

    The resulting :class:`~.Samplex` built from a circuit with a box with this annotation requires
    a :class:`qiskit.quantum_info.PauliLindbladMap` with ``ref`` to at sample time. The qubits of
    the map are indexed in physical qubit order, in other words, the order of the qubits in the
    outer-most circuit, restricted to those used by the box.

    Args:
        ref: A unique identifier of the map from which to inject noise.
        modifier_ref: A unique identifer for modifiers to apply to the noise map before injection.
    """

    namespace = "samplomatic.inject_noise"

    __slots__ = ("ref", "modifier_ref")

    def __init__(self, ref: StrRef, modifier_ref: StrRef = ""):
        self.ref = ref
        self.modifier_ref = modifier_ref

    def __eq__(self, other):
        return (
            isinstance(other, InjectNoise)
            and self.ref == other.ref
            and self.modifier_ref == other.modifier_ref
        )

    def __hash__(self):
        return hash((self.ref, self.modifier_ref))
