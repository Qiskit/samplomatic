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

import numpy as np
import pytest
from qiskit.circuit import Parameter

from samplomatic.exceptions import ParameterError
from samplomatic.samplex import ParameterExpressionTable


def test_empty():
    """Test empty construction has the correct behaviour."""
    table = ParameterExpressionTable()
    assert table.num_expressions == 0
    assert table.num_parameters == 0
    assert isinstance(table.parameters, list) and not table.parameters
    assert np.array_equal(table.evaluate([]), np.array([]))
    assert np.array_equal(table.evaluate({}), np.array([]))


def test_append_fails():
    """Test the append method fails when expected."""
    table = ParameterExpressionTable()
    table.append(b := Parameter("b"))

    # appending the same instance is allowed
    table.append(b)

    with pytest.raises(ParameterError, match="A parameter with name 'b' already exists"):
        table.append(Parameter("a") + Parameter("b"))

    # ensure there are no side-effects of failing to add an expression
    assert table.num_expressions == 2
    assert "a" not in {parameter.name for parameter in table.parameters}


def test_append():
    """Test the append method."""
    a = Parameter("a")
    b = Parameter("b")
    c = Parameter("c")
    table = ParameterExpressionTable()

    assert table.append(b) == 0
    assert table.num_expressions == 1
    assert table.parameters == [b]

    assert table.append(b) == 1
    assert table.num_expressions == 2
    assert table.parameters == [b]

    assert table.append(a) == 2
    assert table.num_expressions == 3
    assert table.parameters == [a, b]

    assert table.append(c + a + b) == 3
    assert table.num_expressions == 4
    assert table.parameters == [a, b, c]


def test_evaluate():
    """Test the evaluate method."""
    a = Parameter("a")
    b = Parameter("b")
    c = Parameter("c")
    table = ParameterExpressionTable()

    table.append(a + b)
    table.append(b + c)
    table.append(a)
    table.append(b)
    table.append(a)
    table.append(a * b * c)

    assert np.array_equal(table.evaluate([1, 2, 3]), np.array([3.0, 5, 1, 2, 1, 6]))
    assert np.array_equal(table.evaluate({a: 2, b: 3, c: 4}), np.array([5.0, 7, 2, 3, 2, 24]))


def test_evaluate_fails():
    """Test the evaluate method fails when expected."""
    a = Parameter("a")
    b = Parameter("b")
    c = Parameter("c")
    table = ParameterExpressionTable()

    table.append(a + b)
    table.append(b + c)
    table.append(a)
    table.append(b)
    table.append(a)
    table.append(a * b * c)

    with pytest.raises(ParameterError, match="Expecting 3 parameters but received 1"):
        table.evaluate([2])

    with pytest.raises(ParameterError, match="Expecting 3 parameters but received 2"):
        table.evaluate({a: 1, b: 2})

    with pytest.raises(ParameterError, match="Missing value for Parameter"):
        table.evaluate({a: 1, b: 2, Parameter("d"): 3})
