# This code is a Qiskit project.
#
# (C) Copyright IBM 2025, 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""DistributionSamplingNode"""

from ...aliases import NumSubsystems, RegisterName
from ...distributions import Distribution
from ...virtual_registers import VirtualType
from .sampling_node import SamplingNode


class DistributionSamplingNode(SamplingNode):
    """A node that produces samples from a distribution.

    Args:
        register_name: The name of the register to store the samples.
        distribution: The distribution to draw samples from.
    """

    def __init__(
        self,
        register_name: RegisterName,
        distribution: Distribution,
    ):
        self._register_name = register_name
        self._distribution = distribution

    @property
    def outgoing_register_type(self) -> VirtualType:
        return self._distribution.register_type

    def instantiates(self) -> dict[RegisterName, tuple[NumSubsystems, VirtualType]]:
        distribution_info = (self._distribution.num_subsystems, self._distribution.register_type)
        return {
            self._register_name: distribution_info,
        }

    def sample(self, registers, rng, inputs, num_randomizations):
        samples = self._distribution.sample(num_randomizations, rng)
        registers[self._register_name] = samples

    def __eq__(self, other):
        return (
            isinstance(other, DistributionSamplingNode)
            and self._register_name == other._register_name
            and self._distribution == other._distribution
        )

    def get_style(self):
        return (
            super()
            .get_style()
            .append_data("Register", repr(self._register_name))
            .append_data("Distribution", repr(self._distribution))
        )
