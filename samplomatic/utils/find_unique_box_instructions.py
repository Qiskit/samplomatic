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

"""find_unique_box_instructions"""

from __future__ import annotations

from collections.abc import Callable, Iterable

from qiskit.circuit import Annotation

from ..aliases import CircuitInstruction
from ..annotations import InjectNoise, Twirl
from .box_key import BoxKey
from .undress_box import undress_box


def default_normalize_annotations(annotations: Iterable[Annotation]) -> list[Annotation]:
    """Keep only ``Twirl`` and ``InjectNoise`` annotations and returned normalized forms.

    For :class:`Twirl` annotations, it creates a new instance with the same group, dressing, and
    decomposition. For :class:`InjectNoise` annotations, it creates a new instance with the same
    ``ref`` and default ``modifier_ref``.

    Args:
        annotations: The annotation to normalize.

    Returns:
        The normalized annotations.
    """
    normalized_annotations = []
    for annot in annotations:
        if isinstance(annot, Twirl):
            normalized_annotations.append(
                Twirl(group=annot.group, dressing=annot.dressing, decomposition=annot.decomposition)
            )
        elif isinstance(annot, InjectNoise):
            normalized_annotations.append(InjectNoise(ref=annot.ref))
    return normalized_annotations


def find_unique_box_instructions(
    instructions: Iterable[CircuitInstruction],
    undress_boxes: bool = True,
    normalize_annotations: Callable[[Iterable[Annotation]], list[Annotation]] | None = None,
) -> list[CircuitInstruction]:
    """Return instructions that contains unique boxes.

    This function iterates through the given ``instructions``, identifying those that contain a
    :class:`.~BoxOp` operation and comparing them based on their content and annotations. It
    returns a list of instructions that contains unique boxes. Optionally, it allows undressing
    the boxes before comparison, as well as normalizing their annotations to ignore irrelevant
    fields.

    Args:
        instructions: The instructions to iterate through.
        undress_boxes: Whether to call the :meth:`~.undress_box` method on each box before
            comparison.
        normalize_annotations: A callable mapping annotations to annotations, which is applied to
            the annotations of each box before comparison. If ``None``, it discards every
            annotation that is not of type ``Twirl`` and ``InjectNoise``, and it resets the
            ``modifier_ref`` field of ``InjectNoise`` annotations to the default value.

    Returns:
        A list of unique instructions.
    """
    normalize_annotations = normalize_annotations or default_normalize_annotations

    instr_dict: dict[BoxKey, CircuitInstruction] = {}
    for instr in instructions:
        if instr.name != "box":
            continue

        box = (
            undress_box(instr.operation)
            if undress_boxes
            else instr.operation.copy()  # Copy to avoid modifying the original box
        )
        box.annotations = normalize_annotations(instr.operation.annotations)

        new_instr = CircuitInstruction(box, instr.qubits, instr.clbits)
        instr_dict[BoxKey(new_instr)] = new_instr

    return list(instr_dict.values())
