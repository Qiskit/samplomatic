# This code is a Qiskit project.
#
# (C) Copyright IBM 2025-2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""BoxBuilder"""

from typing import TypeAlias

import numpy as np
from qiskit.circuit import Barrier

from samplomatic.constants import SUPPORTED_2Q_FRACTIONAL_GATES

from ..aliases import DAGOpNode, ParamIndices
from ..annotations import GATE_DEPENDENT_TWIRLING_GROUPS, GroupMode, InjectionSite
from ..distributions import GROUP_TO_DISTRIBUTION
from ..exceptions import BuildError
from ..pre_samplex import PreSamplex
from ..trace_info import TraceInfo
from ..virtual_registers import VirtualType
from .builder import Builder
from .specs import CollectionSpec, EmissionSpec, InstructionMode
from .template_state import TemplateState

ParsableType: TypeAlias = DAGOpNode | None
"""Types the :meth:`~.BoxBuilder.parse` method is expected to receive.

Here, ``None`` is the sentinel used to denote the transition from
easy to hard gates within a dressed box.
"""


class BoxBuilder(Builder[TemplateState, PreSamplex, ParsableType]):
    """Builds dressed boxes."""

    def __init__(self, collection: CollectionSpec, emission: EmissionSpec):
        super().__init__()

        self.collection = collection
        self.emission = emission

    @property
    def _trace_info(self) -> TraceInfo | None:
        """Return a TraceInfo from this box's emission, or None if debug is off or no refs."""
        if not self.template_state.debug:
            return None
        return TraceInfo.from_emission_trace_refs(self.emission.trace_refs)

    def _append_dressed_layer(self) -> ParamIndices:
        """Add a dressed layer."""
        qubits = self.collection.qubits
        try:
            remapped_qubits = [
                list(map(lambda k: self.template_state.qubit_map[k], subsys)) for subsys in qubits
            ]
        except KeyError:
            not_found = {
                qubit
                for subsys in qubits
                for qubit in subsys
                if qubit not in self.template_state.qubit_map
            }
            raise BuildError(
                f"The qubits '{not_found}' could not be found when recursing into a box of the "
                "input circuit."
            ) from KeyError

        param_idx_start = self.template_state.param_iter.idx
        num_params = len(qubits) * self.collection.synth.num_params
        param_idxs = np.arange(param_idx_start, param_idx_start + num_params, dtype=np.intp)

        for subsys_remapped_qubits in remapped_qubits:
            for instr in self.collection.synth.make_template(
                subsys_remapped_qubits, self.template_state.param_iter
            ):
                new_qubits = self.template_state.qubits(instr.qubits)
                self.template_state.template.apply_operation_back(instr.operation, new_qubits)

        return param_idxs.reshape(len(qubits), -1)

    def _append_barrier(self, label: str):
        label = (
            f"{label}{'_'.join(map(str, self.template_state.scope_idx))}{self.emission.trace_label}"
        )
        all_qubits = self.template_state.qubits()
        self.template_state.template.apply_operation_back(
            Barrier(len(all_qubits), label), all_qubits
        )

    def _emit_twirl(self):
        if (twirl_type := self.emission.twirl_type) is None:
            return
        trace_info = self._trace_info
        if twirl_type in GATE_DEPENDENT_TWIRLING_GROUPS:
            if len(self.emission.gate_dependent_twirls):
                for gate_name, qubits in self.emission.gate_dependent_twirls.items():
                    self.samplex_state.add_emit_twirl(
                        qubits,
                        twirl_type,
                        gate_name,
                        trace_info=trace_info,
                    )
            if len(self.emission.fallback_twirl_qubits):
                self.samplex_state.add_emit_twirl(
                    self.emission.fallback_twirl_qubits,
                    GroupMode.PAULI,
                    trace_info=trace_info,
                )
        else:
            self.samplex_state.add_emit_twirl(
                self.emission.qubits, twirl_type, trace_info=trace_info
            )

    def _validate_fractional_gate(self, instr: DAGOpNode):
        if instr.op.name not in SUPPORTED_2Q_FRACTIONAL_GATES:
            return False

        if self.emission.twirl_type == GroupMode.LOCAL_PAULI:
            return True

        if instr.op.is_parameterized() or not np.allclose(np.abs(instr.op.params), np.pi / 2):
            raise BuildError(
                "Non-Clifford and unbound fractional entanglers are only supported for "
                "Twirl with 'GroupMode LOCAL_PAULI'."
            )

        return False

    def _validate_twirl_supports_measurement(self):
        """Validate that the current twirl type is compatible with measurements."""
        if (twirl_type := self.emission.twirl_type) is None:
            return
        if twirl_type is GroupMode.LOCAL_C1 or (
            twirl_type not in GATE_DEPENDENT_TWIRLING_GROUPS
            and GROUP_TO_DISTRIBUTION[twirl_type](len(self.emission.qubits)).register_type
            != VirtualType.PAULI
        ):
            raise BuildError(f"Cannot use {twirl_type.value} twirl in a box with measurements.")


class LeftBoxBuilder(BoxBuilder):
    """Box builder for left dressings."""

    def __init__(self, collection: CollectionSpec, emission: EmissionSpec):
        super().__init__(collection=collection, emission=emission)

        self._mode = InstructionMode.MULTIPLY

    def parse(self, instr):
        if instr is None:
            trace_info = self._trace_info
            if self.emission.basis_ref:
                self.samplex_state.add_emit_left_basis_change(
                    self.emission.qubits,
                    self.emission.basis_ref,
                    self.emission.basis_change,
                    trace_info=trace_info,
                )
            if self.emission.noise_ref and self.emission.noise_site is InjectionSite.BEFORE:
                self.samplex_state.add_emit_noise_left(
                    self.emission.qubits,
                    self.emission.noise_ref,
                    self.emission.noise_modifier_ref,
                    trace_info=trace_info,
                )
            self._emit_twirl()

            self._mode = InstructionMode.PROPAGATE
            return

        if (name := instr.op.name) == "barrier":
            self.template_state.append_remapped_gate(instr)
            return

        if name.startswith("meas"):
            self._validate_twirl_supports_measurement()
            self.template_state.append_remapped_gate(instr)
            for clbit in instr.cargs:
                clbit_idx = self.template_state.template.find_bit(clbit)[0]
                self.samplex_state.add_measure_propagate(instr, clbit_idx, self._trace_info)
            return

        if name.startswith("reset"):
            self.template_state.append_remapped_gate(instr)
            self.samplex_state.add_reset_propagate(instr, trace_info=self._trace_info)
            return

        commutant_twirl = False
        if (num_qubits := instr.num_qubits) == 1:
            if self._mode is InstructionMode.PROPAGATE:
                params = self.template_state.append_remapped_gate(instr)
            else:
                params = []
                if instr.op.is_parameterized():
                    params.extend((None, param) for param in instr.op.params)

        elif num_qubits > 1:
            commutant_twirl = commutant_twirl | self._validate_fractional_gate(instr)
            params = self.template_state.append_remapped_gate(instr)
        else:
            raise BuildError(f"Instruction {instr} could not be parsed.")

        self.samplex_state.add_propagate(
            instr,
            self._mode,
            params,
            trace_info=self._trace_info,
            commutant_twirl=commutant_twirl,
        )

    def lhs(self):
        self._append_barrier("L")
        param_idxs = self._append_dressed_layer()
        self.samplex_state.add_collect(
            self.collection.qubits,
            self.collection.synth,
            param_idxs,
            trace_info=self._trace_info,
        )
        self._append_barrier("M")

    def rhs(self):
        self._append_barrier("R")

        trace_info = self._trace_info
        if self.emission.noise_ref and self.emission.noise_site is InjectionSite.AFTER:
            self.samplex_state.add_emit_noise_left(
                self.emission.qubits,
                self.emission.noise_ref,
                self.emission.noise_modifier_ref,
                trace_info=trace_info,
            )

    @staticmethod
    def yield_from_dag(dag):
        qubits = set(dag.qubits)

        hard = []
        for node in dag.topological_op_nodes():
            if (
                qubits.issuperset(node.qargs)
                and node.is_standard_gate()
                and node.op.num_qubits == 1
            ):
                yield node
            else:
                hard.append(node)
                qubits.difference_update(node.qargs)

        yield None
        yield from hard


class RightBoxBuilder(BoxBuilder):
    """Box builder for right dressings."""

    def __init__(self, collection: CollectionSpec, emission: EmissionSpec):
        super().__init__(collection=collection, emission=emission)

        self._mode = InstructionMode.PROPAGATE

    def parse(self, instr):
        if instr is None:
            trace_info = self._trace_info
            if self.emission.noise_ref and self.emission.noise_site is InjectionSite.AFTER:
                self.samplex_state.add_emit_noise_right(
                    self.emission.qubits,
                    self.emission.noise_ref,
                    self.emission.noise_modifier_ref,
                    trace_info=trace_info,
                )
            if self.emission.basis_ref:
                self.samplex_state.add_emit_right_basis_change(
                    self.emission.qubits,
                    self.emission.basis_ref,
                    self.emission.basis_change,
                    trace_info=trace_info,
                )
            self._mode = InstructionMode.MULTIPLY
            return

        if (name := instr.op.name).startswith("barrier"):
            self.template_state.append_remapped_gate(instr)
            return

        if name.startswith("meas"):
            self._validate_twirl_supports_measurement()
            self.template_state.append_remapped_gate(instr)
            for clbit in instr.cargs:
                clbit_idx = self.template_state.template.find_bit(clbit)[0]
                self.samplex_state.add_measure_propagate(instr, clbit_idx, self._trace_info)
            return

        if name.startswith("reset"):
            self.template_state.append_remapped_gate(instr)
            self.samplex_state.add_reset_propagate(instr, trace_info=self._trace_info)
            return

        commutant_twirl = False
        if (num_qubits := instr.num_qubits) == 1:
            # the action of this single-qubit gate will be absorbed into the dressing
            if self._mode is InstructionMode.PROPAGATE:
                params = self.template_state.append_remapped_gate(instr)
            else:
                params = []
                if instr.op.is_parameterized():
                    params.extend((None, param) for param in instr.op.params)

        elif num_qubits > 1:
            commutant_twirl = commutant_twirl | self._validate_fractional_gate(instr)
            params = self.template_state.append_remapped_gate(instr)
        else:
            raise BuildError(f"Instruction {instr} could not be parsed.")

        self.samplex_state.add_propagate(
            instr,
            self._mode,
            params,
            trace_info=self._trace_info,
            commutant_twirl=commutant_twirl,
        )

    def lhs(self):
        self._append_barrier("L")
        trace_info = self._trace_info
        self._emit_twirl()
        if self.emission.noise_ref and self.emission.noise_site is InjectionSite.BEFORE:
            self.samplex_state.add_emit_noise_right(
                self.emission.qubits,
                self.emission.noise_ref,
                self.emission.noise_modifier_ref,
                trace_info=trace_info,
            )

    def rhs(self):
        self._append_barrier("M")
        param_idxs = self._append_dressed_layer()
        self.samplex_state.add_collect(
            self.collection.qubits,
            self.collection.synth,
            param_idxs,
            trace_info=self._trace_info,
        )
        self._append_barrier("R")

    @staticmethod
    def yield_from_dag(dag):
        qubits = set(dag.qubits)

        easy = []
        hard = []
        for node in dag.reverse_ops().topological_op_nodes():
            if (
                qubits.issuperset(node.qargs)
                and node.is_standard_gate()
                and node.op.num_qubits == 1
            ):
                easy.append(node)
            else:
                hard.append(node)
                qubits.difference_update(node.qargs)

        yield from reversed(hard)
        yield None
        yield from reversed(easy)
