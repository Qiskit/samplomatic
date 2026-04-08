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

"""Test that debug=True propagates trace info into samplex nodes."""

from qiskit.circuit import QuantumCircuit

from samplomatic import build
from samplomatic.annotations import Tag, Twirl
from samplomatic.trace_info import TraceInfo


def _tagged_circuit(ref: str | None = "my_box", n_qubits: int = 2) -> QuantumCircuit:
    """Return a simple valid 2-box circuit. The first box is optionally tagged."""
    circuit = QuantumCircuit(n_qubits)
    qubits = list(range(n_qubits))
    annotations = [Twirl()]
    if ref is not None:
        annotations.append(Tag(ref=ref))
    with circuit.box(annotations):
        circuit.noop(*qubits)
    with circuit.box([Twirl(dressing="right")]):
        circuit.noop(*qubits)
    return circuit


def test_trace_info_absent_by_default():
    """Without debug=True, all nodes have trace_info=None."""
    _, samplex = build(_tagged_circuit())
    for node in samplex.graph.nodes():
        assert node.trace_info is None


def test_trace_info_populated_with_debug():
    """With debug=True, nodes carry the tag ref from the box."""
    _, samplex = build(_tagged_circuit(), debug=True)
    nodes_with_trace = [n for n in samplex.graph.nodes() if n.trace_info is not None]
    assert len(nodes_with_trace) > 0

    for node in nodes_with_trace:
        assert isinstance(node.trace_info, TraceInfo)
        assert "tag" in node.trace_info.trace_refs
        assert "my_box" in node.trace_info.trace_refs["tag"]


def test_trace_info_absent_when_no_tag():
    """With debug=True but no Tag annotation, nodes have no trace info."""
    _, samplex = build(_tagged_circuit(ref=None), debug=True)
    for node in samplex.graph.nodes():
        assert node.trace_info is None


def test_trace_info_merged_across_boxes():
    """Merged propagation nodes carry the union of tag refs from contributing boxes."""
    # Two identical boxes on different qubit pairs — their PrePropagate nodes will be merged.
    circuit = QuantumCircuit(4)
    with circuit.box([Twirl(), Tag(ref="boxA")]):
        circuit.noop(0, 1)
    with circuit.box([Twirl(), Tag(ref="boxB")]):
        circuit.noop(2, 3)
    with circuit.box([Twirl(dressing="right")]):
        circuit.noop(0, 1, 2, 3)

    _, samplex = build(circuit, debug=True)
    nodes_with_trace = [n for n in samplex.graph.nodes() if n.trace_info is not None]
    assert len(nodes_with_trace) > 0

    all_tags: set[str] = set()
    for node in nodes_with_trace:
        all_tags.update(node.trace_info.trace_refs.get("tag", set()))

    assert "boxA" in all_tags
    assert "boxB" in all_tags
