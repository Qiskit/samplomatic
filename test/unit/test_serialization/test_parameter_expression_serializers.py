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

import orjson
import pytest
from qiskit.circuit import Parameter, ParameterVector

from samplomatic.samplex import ParameterExpressionTable
from samplomatic.serialization.parameter_expression_serializer import (
    ParameterExpressionTableSerializer,
)
from samplomatic.serialization.type_serializer import TypeSerializer


@pytest.mark.parametrize("ssv", ParameterExpressionTableSerializer.SSVS)
def test_change_basis_serializer_round_trip(ssv):
    table = ParameterExpressionTable()
    table.append(sum(ParameterVector("p", 10)))
    table.append(Parameter("a") - Parameter("b"))
    data = ParameterExpressionTableSerializer.serialize(table, ssv)
    orjson.dumps(data)
    assert table == TypeSerializer.deserialize(data)


def test_ssv3_format():
    """Test that SSV3 uses values_base64 (not circuit_base64) and includes qpy version."""
    table = ParameterExpressionTable()
    table.append(Parameter("x") + Parameter("y"))
    data = ParameterExpressionTableSerializer.serialize(table, ssv=3)
    assert "values_base64" in data
    assert "circuit_base64" not in data
    assert "qpy" in data
    assert int(data["qpy"]) > 0
