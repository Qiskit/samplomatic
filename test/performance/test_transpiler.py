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

"""Test the transpiler."""

import pytest
from qiskit.transpiler import PassManager
from qiskit.transpiler.passes import RemoveBarriers

from samplomatic.transpiler import generate_boxing_pass_manager
from samplomatic.transpiler.passes import InlineBoxes

from .utils import make_layered_circuit


@pytest.mark.parametrize(
    ("num_qubits", "num_gates"),
    [
        pytest.param(
            96,
            5_000,
            marks=pytest.mark.skipif(
                "config.getoption('--performance-light')", reason="smoke test only"
            ),
        ),
        pytest.param(
            10,
            100,
            marks=pytest.mark.skipif(
                "not config.getoption('--performance-light')", reason="performance test only"
            ),
        ),
    ],
)
@pytest.mark.parametrize("inject_noise_strategy", ["no_modification", "individual_modification"])
def test_transpiling_5k_circuit(benchmark, num_qubits, num_gates, inject_noise_strategy):
    """Test the boxing pass manager performance."""
    num_boxes = num_gates // (num_qubits // 2)
    boxed_circuit = make_layered_circuit(num_qubits, num_boxes)
    unboxed_circuit = PassManager([InlineBoxes()]).run(boxed_circuit)
    pm = generate_boxing_pass_manager(inject_noise_strategy=inject_noise_strategy)

    transpiled_circuit = benchmark(pm.run, unboxed_circuit)

    assert PassManager([RemoveBarriers()]).run(unboxed_circuit) == PassManager(
        [InlineBoxes(), RemoveBarriers()]
    ).run(transpiled_circuit)
