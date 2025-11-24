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

"""TwirlSamplingNode"""

from ...aliases import NumSubsystems, RegisterName
from ...annotations import VirtualType
from ...distributions import Distribution
from .sampling_node import SamplingNode


class TwirlSamplingNode(SamplingNode):
    """A node that produces samples for twirling.

    Args:
        lhs_register_name: The name of the register to store the samples.
        rhs_register_name: The name of the register to store the inverses of the samples.
        distribution: The distribution to draw samples from.
    """

    def __init__(
        self,
        lhs_register_name: RegisterName,
        rhs_register_name: RegisterName,
        distribution: Distribution,
    ):
        self._lhs_register_name = lhs_register_name
        self._rhs_register_name = rhs_register_name
        self._distribution = distribution

    @property
    def outgoing_register_type(self) -> VirtualType:
        return self._distribution.register_type

    def instantiates(self) -> dict[RegisterName, tuple[NumSubsystems, VirtualType]]:
        distribution_info = (self._distribution.num_subsystems, self._distribution.register_type)
        return {
            self._lhs_register_name: distribution_info,
            self._rhs_register_name: distribution_info,
        }

    def sample(self, registers, rng, inputs, num_randomizations):
        samples = self._distribution.sample(num_randomizations, rng)
        registers[self._lhs_register_name] = samples
        registers[self._rhs_register_name] = samples.invert()

    def __eq__(self, other):
        return (
            isinstance(other, TwirlSamplingNode)
            and self._lhs_register_name == other._lhs_register_name
            and self._rhs_register_name == other._rhs_register_name
            and self._distribution == other._distribution
        )

    def get_style(self):
        return (
            super()
            .get_style()
            .append_data("LHS Register", repr(self._lhs_register_name))
            .append_data("RHS Register", repr(self._rhs_register_name))
            .append_data("Distribution", repr(self._distribution))
        )
