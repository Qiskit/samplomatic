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

"""TwirlingStrategy"""

from __future__ import annotations

from enum import Enum
from typing import Literal, Union

from ..aliases import TypeAlias


class TwirlingStrategy(str, Enum):
    """The twirling strategies supported by the boxing pass manager."""

    ACTIVE = "active"
    ACTIVE_ACCUM = "active_accum"
    ACTIVE_CIRCUIT = "active_circuit"
    ALL = "all"


TwirlingStrategyLiteral: TypeAlias = Union[
    TwirlingStrategy, Literal["active", "active_accum", "all", "active_circuit"]
]

"""The twirling strategies supported by the boxing pass manager.

The boxing pass manager begins by constructing twirling boxes that contain one layer of multi-qubit
gates or measurements, preceeded by all of the adjacent single-qubit gates. Next, it proceeds by
adding idling qubits to the boxes based on the selected twirling strategy. The following options are
supported:

 * ``'active'``: No idling qubit is added to the boxes, meaning that every box only twirls the
    qubits that are active within the box.
 * ``'active-accum'``: Idling qubits are added so that each individual box twirls the union of the
    instructions qubits in the circuit up to the current twirled box.
 * ``'active-circuit'``: Idling qubits are added so that each individual box twirls all of the
    instructions qubits in the circuit.
 * ``'all'``: Idling qubits are added so that each individual box twirls all of the qubits in
    the circuit.
"""
