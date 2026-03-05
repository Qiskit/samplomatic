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
    """Marker annotation to include trace information in barrier labels.

    When present on a ``box`` instruction, the barriers emitted during :func:`~samplomatic.build`
    include trace information.

    The following information is included:

    * If there's an :class:`~.InjectNoise` annotation present, includes its
      :attr:`~InjectNoise.ref`.
    """

    namespace = "samplomatic.trace_box"

    def __eq__(self, other):
        return isinstance(other, TraceBox)

    def __hash__(self):
        return hash(TraceBox)

    def __repr__(self):
        return f"{type(self).__name__}()"
