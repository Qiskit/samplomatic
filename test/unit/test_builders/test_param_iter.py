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

import pytest
from qiskit.circuit import Parameter

from samplomatic.builders.param_iter import ParamIter


def test_construction():
    """Test construction and attributes."""
    param_iter = ParamIter(50, "a")
    assert param_iter.name_template == "a{:02}"
    assert param_iter.max_num == 50
    assert param_iter.idx == 0


def test_next():
    """Test the next dunder."""
    param_iter = ParamIter(3)
    assert param_iter.idx == 0
    assert next(param_iter).name == Parameter("p0").name
    assert param_iter.idx == 1
    assert next(param_iter).name == Parameter("p1").name
    assert param_iter.idx == 2
    assert next(param_iter).name == Parameter("p2").name
    assert param_iter.idx == 3
    with pytest.raises(StopIteration):
        next(param_iter)
    assert param_iter.idx == 3


def test_iterator_is_self():
    """Test that as an iterable a ParamIter is itself."""
    param_iter = ParamIter()
    assert iter(param_iter) is param_iter
