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

"""Annotation editing utility functions"""

from collections.abc import Callable

from qiskit.circuit import Annotation, BoxOp, CircuitInstruction, QuantumCircuit


def map_annotations(
    circuit: QuantumCircuit,
    fn: Callable[[list[Annotation]], list[Annotation]],
) -> QuantumCircuit:
    """Return a new circuit where each box's annotations are replaced by ``fn(annotations)``.

    The callable receives the current list of annotations on the box and must return a new list of
    annotations to use. Non-box instructions are copied unchanged, and the original circuit is not
    mutated.

    Args:
        circuit: The circuit whose box annotations to transform.
        fn: A callable that receives a box's annotation list and returns the replacement list.

    Returns:
        A new circuit with transformed annotations on every box.

    .. plot::
        :include-source:

        from qiskit.circuit import QuantumCircuit
        from samplomatic import Twirl, InjectNoise
        from samplomatic.utils import map_annotations, strip_annotations

        circuit = QuantumCircuit(2)
        with circuit.box([Twirl(), InjectNoise("ref")]):
            circuit.cx(0, 1)

        # Keep only Twirl annotations
        filtered = map_annotations(circuit, lambda anns: [a for a in anns if isinstance(a, Twirl)])
    """
    new_circuit = circuit.copy_empty_like()
    for instr in circuit.data:
        if instr.operation.name == "box":
            box = instr.operation
            new_annotations = fn(box.annotations)
            new_box = BoxOp(body=box.body, label=box.label, annotations=new_annotations)
            new_circuit.data.append(CircuitInstruction(new_box, instr.qubits, instr.clbits))
        else:
            new_circuit.data.append(instr)
    return new_circuit


def strip_annotations(circuit: QuantumCircuit) -> QuantumCircuit:
    """Return a new circuit with all annotations removed from every box.

    Args:
        circuit: The circuit whose box annotations to strip.

    Returns:
        A new circuit with empty annotation lists on every box.

    .. plot::
        :include-source:

        from qiskit.circuit import QuantumCircuit
        from samplomatic import Twirl
        from samplomatic.utils import strip_annotations

        circuit = QuantumCircuit(2)
        with circuit.box([Twirl()]):
            circuit.cx(0, 1)

        bare = strip_annotations(circuit)
    """
    return map_annotations(circuit, lambda _: [])


def filter_annotations(
    circuit: QuantumCircuit,
    keep: type[Annotation] | tuple[type[Annotation], ...],
) -> QuantumCircuit:
    """Return a new circuit keeping only annotations of the given type(s) on each box.

    Args:
        circuit: The circuit whose box annotations to filter.
        keep: Annotation type or tuple of types to retain.

    Returns:
        A new circuit where each box's annotations contain only instances of ``keep``.

    .. plot::
        :include-source:

        from qiskit.circuit import QuantumCircuit
        from samplomatic import Twirl, InjectNoise
        from samplomatic.utils import filter_annotations

        circuit = QuantumCircuit(2)
        with circuit.box([Twirl(), InjectNoise("ref")]):
            circuit.cx(0, 1)

        twirl_only = filter_annotations(circuit, Twirl)
    """
    return map_annotations(circuit, lambda anns: [a for a in anns if isinstance(a, keep)])


def extend_annotations(circuit: QuantumCircuit, *annotations: Annotation) -> QuantumCircuit:
    """Return a new circuit with the given annotations appended to every box.

    Args:
        circuit: The circuit whose boxes to extend.
        *annotations: One or more annotation instances to append.

    Returns:
        A new circuit where each box's annotations are the original list followed by
        ``annotations``.

    .. plot::
        :include-source:

        from qiskit.circuit import QuantumCircuit
        from samplomatic import Twirl, InjectNoise
        from samplomatic.utils import extend_annotations

        circuit = QuantumCircuit(2)
        with circuit.box([Twirl()]):
            circuit.cx(0, 1)

        with_noise = extend_annotations(circuit, InjectNoise("ref"))
    """
    return map_annotations(circuit, lambda anns: [*anns, *annotations])


def replace_annotations(
    circuit: QuantumCircuit,
    fn: Callable[[Annotation], Annotation | None],
) -> QuantumCircuit:
    """Return a new circuit with annotations replaced or removed according to a callable.

    For each annotation on each box, ``fn`` is called with the annotation instance. If ``fn``
    returns an :class:`~qiskit.circuit.Annotation`, that value replaces the original. If ``fn``
    returns ``None``, the annotation is removed.

    Args:
        circuit: The circuit whose box annotations to replace.
        fn: A callable that receives each annotation and returns either a replacement annotation
            or ``None`` to delete it.

    Returns:
        A new circuit with annotations replaced or removed per ``fn``.

    .. plot::
        :include-source:

        from qiskit.circuit import QuantumCircuit
        from samplomatic import Twirl
        from samplomatic.utils import replace_annotations

        circuit = QuantumCircuit(2)
        with circuit.box([Twirl(group="pauli")]):
            circuit.cx(0, 1)

        # Replace Twirl annotations, delete anything else
        updated = replace_annotations(
            circuit, lambda a: Twirl(group="local_c1") if isinstance(a, Twirl) else None
        )
    """

    def _replace(anns: list[Annotation]) -> list[Annotation]:
        result = []
        for a in anns:
            out = fn(a)
            if out is not None:
                result.append(out)
        return result

    return map_annotations(circuit, _replace)
