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

"""TraceBox"""

from qiskit.circuit import Annotation


class TraceBox(Annotation):
    """Annotation to include trace information in barrier labels.

    When present on a ``box`` instruction, the barriers emitted during :func:`~samplomatic.build`
    include trace information.

    The following information is included:

    * The :attr:`ref` of this annotation if it's set.
    * The :attr:`~InjectNoise.ref` of an :class:`~.InjectNoise` if there is one on the box.

    Args:
        ref: A reference string to include in barrier labels.
    """

    namespace = "samplomatic.trace_box"

    def __init__(self, ref: str = ""):
        self._ref = ref

    @property
    def ref(self) -> str:
        """The reference string to include in barrier labels."""
        return self._ref

    def __eq__(self, other):
        return isinstance(other, TraceBox) and self._ref == other._ref

    def __hash__(self):
        return hash((TraceBox, self._ref))

    def __repr__(self):
        args = f"ref={self._ref!r}" if self._ref else ""
        return f"{type(self).__name__}({args})"
