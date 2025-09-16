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

"""ParamIter"""

from ..aliases import Parameter, Self


class ParamIter:
    """Iterator over new :class:`~.Parameter` instances in sorted order."""

    __slots__ = ("idx", "name_template", "max_num")

    def __init__(self, max_num: int = 1_000, prefix: str = "p"):
        num_digits = len(str(max_num))
        self.max_num = max_num
        self.name_template: str = f"{prefix}{{:0{num_digits}}}"
        self.idx: int = 0

    def __next__(self) -> Parameter:
        if (idx := self.idx) >= self.max_num:
            raise StopIteration
        self.idx += 1
        return Parameter(self.name_template.format(idx))

    def __iter__(self) -> Self:
        return self
