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

"""Test RightBoxSamplexBuilder"""

from qiskit.circuit import QuantumCircuit

from samplomatic import Twirl
from samplomatic.builders import pre_build


class TestRightBoxBuilder:
    """Test Box Builders"""

    def test_if_else(self):
        """Test the build result of if-else.

        Because it is a bit difficult to do by hand, we use the full pre_build.
        """
        circuit = QuantumCircuit(1, 1)
        circuit.measure(0, 0)
        with circuit.box([Twirl(dressing="left")]):
            circuit.noop(0)
        with circuit.box([Twirl(dressing="right")]):
            with circuit.if_test((circuit.clbits[0], 1)) as _else:
                circuit.x(0)
            with _else:
                circuit.sx(0)

        _, pre_samplex = pre_build(circuit)
        graph = pre_samplex.graph
        for emit_node in [1, 2]:
            assert not graph.get_edge_data(emit_node, 3).force_register_copy
            assert graph.get_edge_data(emit_node, 6).force_register_copy
        assert graph[3].operation.name == "x"
        assert graph[6].operation.name == "sx"
