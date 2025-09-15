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

"""get_annotation"""

from __future__ import annotations

from qiskit.circuit import Annotation, BoxOp


def get_annotation(box: BoxOp, annotation_type: type[Annotation]) -> Annotation | None:
    """Return a box's first annotation of the given type.

    Args:
        box: The box to return the annotation for.
        annotation_type: The type of the desired annotation.

    Returns:
        The box's first annotation of the given type, or ``None`` if it does not contain an
        annotation of the given type.
    """
    return next((annot for annot in box.annotations if isinstance(annot, annotation_type)), None)
