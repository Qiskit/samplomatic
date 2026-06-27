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

"""Stratification scheduling algorithms.

This subpackage provides six algorithms for solving the stratification problem.
All algorithms accept a :class:`.StratificationInstance` and return a
:class:`.Stratification`.

Algorithms optimising depth first
----------------------------------

- :func:`.greedy_stratify` (A) — classical list scheduling, fastest.
- :func:`.coffman_graham_stratify` (B) — Coffman–Graham with pattern-reuse tiebreaker.

Algorithms optimising pattern count first
------------------------------------------

- :func:`.pattern_batch_stratify` (E) — data-driven peeling; ``|Λ| ≤ |Σ|`` guaranteed.

Exact and stochastic
---------------------

- :func:`.ilp_stratify` (F) — lexicographic ILP via PuLP/CBC (exact baseline).
- :func:`.grasp_stratify` (G) — GRASP randomized multi-start wrapper (bases: A, B).

Post-processing
---------------

- :func:`.refine_stratification` — local-search post-pass (Relocate / Swap / Merge).
"""

from .coffman_graham import coffman_graham_stratify
from .grasp import grasp_stratify
from .greedy import greedy_stratify
from .ilp import ilp_stratify
from .pattern_batch import pattern_batch_stratify
from .refine import refine_stratification

__all__ = [
    "coffman_graham_stratify",
    "grasp_stratify",
    "greedy_stratify",
    "ilp_stratify",
    "pattern_batch_stratify",
    "refine_stratification",
]
