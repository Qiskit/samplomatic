# This code is a Qiskit project.
#
# (C) Copyright IBM 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Quantum Programs.

Overview
--------

A :class:`~.QuantumProgram` is an ordered collection of items, where each item pairs a single
circuit with the parameter data used to bind it. The program bundles these items together with
shared settings such as the number of ``shots``, the classical-register measurement level, and
optional noise maps, so that a whole family of related circuits can be described as one object.

Every item is a :class:`~.QuantumProgramItem`, which comes in two flavors depending on how the
circuit's parameters are supplied:

* A :class:`~.CircuitItem` holds a circuit together with an explicit array of
  ``circuit_arguments``. This is the natural choice when the parameter values are already known,
  for instance a parameter sweep laid out on a grid.
* A :class:`~.SamplexItem` holds a circuit together with a :class:`~samplomatic.samplex.Samplex`
  that *generates* the circuit's parameters. This is the natural choice for randomized circuits,
  such as Pauli twirling, where the concrete parameter values are drawn on demand rather than
  fixed in advance.

Shapes and broadcasting
^^^^^^^^^^^^^^^^^^^^^^^^^

Each item has a :attr:`~.QuantumProgramItem.shape`, obtained by broadcasting the *extrinsic*
shapes of its inputs. Input arrays split their axes into extrinsic axes (leftmost, defining the
sweep grid) and intrinsic axes (rightmost, fixed by the data type). For example,
``circuit_arguments`` for a circuit with ``n`` parameters has intrinsic shape ``(n,)``, so an
array of shape ``(5, 3, n)`` has extrinsic shape ``(5, 3)``. For a :class:`~.SamplexItem`, the
``shape`` argument can enlarge the extrinsic grid beyond what the samplex arguments imply, with
the extra axes enumerating independent randomizations.

Results
^^^^^^^

The :class:`~.QuantumProgramResult` class collects the results associated with a program. This class
mirrors the program's structure: it holds one :class:`~.QuantumProgramItemResult` per program
item, in the same order. Each item result behaves like a mapping from output names to arrays,
and carries per-item metadata alongside the shared, program-level metadata stored on the
:class:`~.QuantumProgramResult`.
"""

from .quantum_program import CircuitItem, QuantumProgram, QuantumProgramItem, SamplexItem
from .quantum_program_result import (
    ChunkPart,
    ChunkSpan,
    ChunkTiming,
    QuantumProgramItemResult,
    QuantumProgramResult,
)
