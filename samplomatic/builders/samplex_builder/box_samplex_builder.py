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

"""BoxSamplexBuilder"""

from __future__ import annotations

from copy import deepcopy

from ...aliases import CircuitInstruction
from ...exceptions import SamplexBuildError
from ...partition import QubitPartition
from ...pre_samplex import DanglerMatch, PreSamplex
from ...pre_samplex.graph_data import PreCollect, PrePropagate
from ..builder import Builder
from ..specs import CollectionSpec, EmissionSpec, InstructionSpec, VirtualType


class BoxSamplexBuilder(Builder[PreSamplex, None]):
    """Builds dressed boxes."""

    def __init__(self, collection: CollectionSpec, emission: EmissionSpec):
        super().__init__()

        self.collection = collection
        self.emission = emission
        self.already_collected_qubits = set()


class LeftBoxSamplexBuilder(BoxSamplexBuilder):
    """Box builder for left dressings."""

    def __init__(self, collection: CollectionSpec, emission: EmissionSpec):
        super().__init__(collection, emission)
        self.measured_qubits = QubitPartition(1, [])
        self.clbit_idxs = []
        self.collection_node_idx = None

    def parse(self, instr: CircuitInstruction, spec: InstructionSpec):
        if instr.operation.name.startswith("if_else"):
            if any(qubit in self.already_collected_qubits for qubit in instr.qubits):
                raise SamplexBuildError(
                    "No instruction can appear before a conditional in a left-dressed box."
                )
            self.state.verify_no_twirled_clbits(spec.clbit_idxs)

            # Mark all qubits as already collected.
            # Important to do first, because of nested calls to parse.
            self.already_collected_qubits.update(instr.qubits)
            if_specs, if_params, else_specs, else_params = spec.if_else
            qubits_partition = QubitPartition.from_elements(instr.qubits)
            # Both branches need to attach to the same danglers, so we copy the original danglers
            original_danglers = deepcopy(self.state.get_all_danglers())
            self.state.add_collect(qubits_partition, self.collection.synth, if_params)
            for sub_instr, sub_spec in zip(instr.operation.params[0], if_specs):
                self.parse(sub_instr, sub_spec)

            # use list() to iterate the generator expression immediately; state may change
            true_branch_danglers = list(
                self.state.find_danglers(
                    DanglerMatch(node_types=(PreCollect, PrePropagate)),
                    self.state.qubits_to_indices(qubits_partition),
                )
            )
            # We need to track all nodes which are added from this point on, to know which
            # nodes have to force copy of registers. There is currently no efficient way of
            # doing this, so we are forced to compare the set of all nodes before and after.
            # If we assume no node removal, we can simplify and look at the max
            # node idx before and after.
            # If we return node indices from parse() we can also simplify this.
            after_if_node_idxs = set(self.state.graph.node_indices())

            self.state.set_all_danglers(*original_danglers)
            self.state.add_collect(qubits_partition, self.collection.synth, else_params)
            if instr.operation.params[1] is not None:
                for sub_instr, sub_spec in zip(instr.operation.params[1], else_specs):
                    self.parse(sub_instr, sub_spec)
            # Right now, all of the qubits have the else branch nodes as dangling.
            # We need to add the danglers of the true branch.
            # Note that by construction all of these danglers are new, and their type is forced,
            # as they don't follow a measurement.
            for node_idx, subsystems in true_branch_danglers:
                self.state.add_dangler(
                    subsystems.all_elements,
                    node_idx,
                )
            # We don't want the else branch to share views with the if branch.
            self.state.add_force_copy_nodes(
                idx for idx in self.state.graph.node_indices() if idx not in after_if_node_idxs
            )
            return

        if to_be_collected := [
            qubit for qubit in instr.qubits if qubit not in self.already_collected_qubits
        ]:
            self.collection_node_idx = self.state.add_collect(
                QubitPartition.from_elements(to_be_collected),
                self.collection.synth,
                spec.param_idxs,
                self.collection_node_idx,
            )
            self.already_collected_qubits.update(to_be_collected)

        if instr.operation.name.startswith("meas"):
            for qubit in instr.qubits:
                if (qubit,) not in self.measured_qubits:
                    self.measured_qubits.add((qubit,))
                else:
                    raise SamplexBuildError(
                        "Cannot measure the same qubit twice in a twirling box."
                    )
            self.clbit_idxs.extend(spec.clbit_idxs)

        else:
            if self.measured_qubits.overlaps_with(instr.qubits):
                # TODO: What about delays? barriers?
                raise SamplexBuildError(
                    f"Instruction {instr} happens after a measurement. No operations allowed "
                    "after a measurement in a measurement twirling box."
                )
            self.state.add_propagate(instr, spec)

    def lhs(self, *_):
        # Collections are added incrementally.
        pass

    def rhs(self, spec: InstructionSpec):
        if remaining_qubits := self.collection.qubits.difference(self.already_collected_qubits):
            self.state.add_collect(
                remaining_qubits, self.collection.synth, spec.param_idxs, self.collection_node_idx
            )
        if self.emission.noise_ref:
            self.state.add_emit_noise_left(
                self.emission.qubits, self.emission.noise_ref, self.emission.noise_modifier_ref
            )
        if self.emission.basis_ref:
            self.state.add_emit_meas_basis_transform(self.emission.qubits, self.emission.basis_ref)
        if twirl_type := self.emission.twirl_register_type:
            self.state.add_emit_twirl(self.emission.qubits, twirl_type)
            if len(self.measured_qubits) != 0:
                if twirl_type != VirtualType.PAULI:
                    raise SamplexBuildError(
                        f"Cannot use {twirl_type.value} twirl in a box with measurements."
                    )
                self.state.add_z2_collect(self.measured_qubits, self.clbit_idxs)


class RightBoxSamplexBuilder(BoxSamplexBuilder):
    """Box builder for right dressings."""

    def parse(self, instr: CircuitInstruction, spec: InstructionSpec):
        if instr.operation.name.startswith("meas"):
            raise SamplexBuildError("Unexpected measurement in a non-measurement box.")
        elif instr.operation.name.startswith("if_else"):
            self.state.verify_no_twirled_clbits(spec.clbit_idxs)
            if_specs, if_params, else_specs, else_params = (
                spec.if_else[0],
                spec.if_else[1],
                spec.if_else[2],
                spec.if_else[3],
            )
            # Both branches need to attach to the same danglers, so we copy the original danglers
            original_danglers = deepcopy(self.state.get_all_danglers())
            for sub_instr, sub_spec in zip(instr.operation.params[0], if_specs):
                self.parse(sub_instr, sub_spec)
            true_collect_idx = self.state.add_collect(
                QubitPartition.from_elements(instr.qubits), self.collection.synth, if_params
            )
            self.state.set_all_danglers(*original_danglers)
            # We don't want the else branch to share views with the if branch
            for danglers_dict in original_danglers:
                for node_idxs in danglers_dict.values():
                    self.state.add_force_copy_nodes(node_idxs)

            if instr.operation.params[1] is not None:
                for sub_instr, sub_spec in zip(instr.operation.params[1], else_specs):
                    self.parse(sub_instr, sub_spec)
            self.state.add_collect(
                QubitPartition.from_elements(instr.qubits), self.collection.synth, else_params
            )
            # Right now, all of the qubits have the false branch collection as dangling.
            # We need to add the true branch collection as a second dangler to all qubits.
            self.state.add_dangler(
                self.state.qubits_to_indices(
                    QubitPartition.from_elements(instr.qubits)
                ).all_elements,
                true_collect_idx,
            )
            # Mark all qubits as already collected
            self.already_collected_qubits.update(instr.qubits)
            # We are done with everything incoming to the else branch,
            # so we can remove the nodes and let them share views now.
            for danglers_dict in original_danglers:
                for node_idxs in danglers_dict.values():
                    self.state.remove_force_copy_nodes(node_idxs)
            return
        self.state.add_propagate(instr, spec)

    def lhs(self, *_):
        if self.emission.basis_ref:
            self.state.add_emit_prep_basis_transform(self.emission.qubits, self.emission.basis_ref)
        if self.emission.noise_ref:
            self.state.add_emit_noise_right(
                self.emission.qubits, self.emission.noise_ref, self.emission.noise_modifier_ref
            )
        if self.emission.twirl_register_type:
            self.state.add_emit_twirl(self.emission.qubits, self.emission.twirl_register_type)

    def rhs(self, spec: InstructionSpec):
        if len(to_collect := self.collection.qubits.difference(self.already_collected_qubits)) > 0:
            self.state.add_collect(to_collect, self.collection.synth, spec.param_idxs)
