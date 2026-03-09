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

"""Tag"""

from qiskit.circuit import Annotation


class Tag(Annotation):
    """Annotation to tag and instruction with a string reference.

    When present on a ``box`` instruction, the barriers emitted during :func:`~samplomatic.build`
    include the ``ref`` of this annotation as part of their label information. In this way, when
    combined with the build function, a tag annotation can be used as a tracing mechanism to
    tie a "barrier sandwich" in a template circuit back to the box it came from in the original
    circuit.

    Args:
        ref: A reference string.
    """

    namespace = "samplomatic.tag"

    def __init__(self, ref: str = ""):
        self._ref = ref

    @property
    def ref(self) -> str:
        """The reference string of this tag."""
        return self._ref

    def __eq__(self, other):
        return isinstance(other, Tag) and self._ref == other._ref

    def __hash__(self):
        return hash((Tag, self._ref))

    def __repr__(self):
        args = f"ref={self._ref!r}" if self._ref else ""
        return f"{type(self).__name__}({args})"
