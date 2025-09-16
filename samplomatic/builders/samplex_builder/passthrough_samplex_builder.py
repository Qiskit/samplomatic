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

"""SamplexPassthroughBuilder"""

from ...aliases import CircuitInstruction
from ...pre_samplex import PreSamplex
from ..builder import Builder
from ..specs import InstructionSpec


class PassthroughSamplexBuilder(Builder[PreSamplex, None]):
    """Samplex builder that passes all instructions through."""

    def parse(self, instr: CircuitInstruction, spec: InstructionSpec):
        if instr.operation.name.startswith("if_else"):
            # No propagation can happen via a conditional, so it plays no role in the samplex.
            self.state.enforce_no_propagation(instr)
            self.state.verify_no_twirled_clbits(spec.clbit_idxs)
            self.state.passthrough_params.extend(spec.params)
        else:
            self.state.add_propagate(instr, spec)

    def lhs(self, *_):
        pass

    def rhs(self, *_):
        pass
