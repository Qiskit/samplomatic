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

import orjson

from ...aliases import NumSubsystems, RegisterName
from ...annotations import VirtualType
from ...distributions import Distribution, HaarU2, UniformPauli
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

    def _to_json_dict(self) -> dict[str, str]:
        if isinstance(self._distribution, HaarU2):
            distribution_type = "haar_u2"
        else:
            distribution_type = "pauli_uniform"
        distribution = {
            "type": distribution_type,
            "num_subsystems": self._distribution.num_subsystems,
        }
        return {
            "node_type": "9",
            "lhs_register_name": self._lhs_register_name,
            "rhs_register_name": self._rhs_register_name,
            "distribution": orjson.dumps(distribution).decode("utf-8"),
        }

    @classmethod
    def _from_json_dict(cls, data: dict[str, str]) -> "TwirlSamplingNode":
        distribution_dict = orjson.loads(data["distribution"])
        if distribution_dict["type"] == "haar_u2":
            distribution = HaarU2(distribution_dict["num_subsystems"])
        else:
            distribution = UniformPauli(distribution_dict["num_subsystems"])
        return cls(data["lhs_register_name"], data["rhs_register_name"], distribution)

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

    def get_style(self):
        return (
            super()
            .get_style()
            .append_data("LHS Register", repr(self._lhs_register_name))
            .append_data("RHS Register", repr(self._rhs_register_name))
            .append_data("Distribution", repr(self._distribution))
        )
