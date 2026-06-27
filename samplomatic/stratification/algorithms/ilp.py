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

"""Algorithm F — lexicographic ILP exact baseline."""

from typing import Literal

import pulp

from ..instance import StratificationInstance
from ..stratification import Stratification
from ._common import assignment_to_stratification, pack_into_layers


def ilp_stratify(
    instance: StratificationInstance,
    *,
    objective: Literal["depth", "pattern"] = "depth",
    time_limit: float | None = None,
    k_max: int | None = None,
) -> Stratification:
    """Stratify ``instance`` using a lexicographic ILP (Algorithm F).

    Encodes layer assignment as a binary program and minimises the primary objective
    (``depth`` or ``pattern``) exactly, then minimises the secondary objective subject
    to the primary being optimal.  Uses the PuLP/CBC solver.

    **Pattern objective note**: the ``pattern`` objective minimises
    ``Σ_{(s,k)} t_{s,k}`` — the total number of label-uses across all layers — which
    is a tractable linear proxy for ``unique_pattern_count``.  It strongly correlates
    with the true pattern count but is not identical to it.  For further exact
    minimisation of ``unique_pattern_count``, apply :func:`.refine_stratification`
    afterwards.

    This function is provided as an exact depth baseline.  For instances with more than
    ~30 edges it may be slow.

    Args:
        instance: The stratification problem to solve.
        objective: Primary objective — ``"depth"`` minimises layer count first, then
            the pattern proxy; ``"pattern"`` minimises the pattern proxy first, then
            layer count.  Defaults to ``"depth"``.
        time_limit: Optional wall-clock time limit in seconds passed to the CBC solver.
            If the solver times out, the best feasible solution found so far is returned.
        k_max: Upper bound on the number of layers used as the ILP index range.  Defaults
            to the depth of :func:`.greedy_stratify` applied to ``instance``.

    Returns:
        A valid :class:`.Stratification`.

    Raises:
        ImportError: If ``pulp`` is not installed.
        RuntimeError: If the ILP is infeasible (should not happen for valid instances).
    """
    if instance.num_edges == 0:
        return Stratification(instance, [])

    from .greedy import greedy_stratify

    n = instance.num_edges
    labels = instance.labels
    alphabet = sorted(instance.alphabet, key=str)  # deterministic ordering
    hg_edges = instance.hypergraph.edges
    arcs = instance.precedence_arcs()

    # Determine k_max
    if k_max is None:
        k_max = greedy_stratify(instance).depth
    K = k_max  # layers indexed 0..K-1

    # Build vertex -> list of edges containing it (for matching constraints)
    vertex_edges: dict[int, list[int]] = {}
    for e, verts in enumerate(hg_edges):
        for v in verts:
            vertex_edges.setdefault(v, []).append(e)

    # Label -> list of edges with that label
    label_edges: dict = {}
    for e, lbl in enumerate(labels):
        label_edges.setdefault(lbl, []).append(e)

    solver_kwargs: dict = {"msg": False}
    if time_limit is not None:
        solver_kwargs["timeLimit"] = time_limit
    solver = pulp.PULP_CBC_CMD(**solver_kwargs)

    def _build_and_solve(
        fixed_primary: int | None = None,
        minimize_secondary: bool = False,
    ) -> tuple[dict[int, int], float | None]:
        """Build and solve the ILP.

        If *fixed_primary* is given, add a constraint fixing the primary objective
        to that value while minimising the secondary objective.

        Returns:
            A ``(depth_of, primary_val)`` pair where ``depth_of`` maps each edge ID
            to its assigned layer index and ``primary_val`` is the primary objective
            value from the solver (or ``None`` if unavailable).
        """
        prob = pulp.LpProblem("stratification", pulp.LpMinimize)

        # x[e][k] = 1 iff edge e is assigned to layer k
        x = [[pulp.LpVariable(f"x_{e}_{k}", cat="Binary") for k in range(K)] for e in range(n)]
        # u[k] = 1 iff layer k is non-empty
        u = [pulp.LpVariable(f"u_{k}", cat="Binary") for k in range(K)]
        # t[s_idx][k] = 1 iff label alphabet[s_idx] appears in layer k
        t = [
            [pulp.LpVariable(f"t_{s_idx}_{k}", cat="Binary") for k in range(K)]
            for s_idx in range(len(alphabet))
        ]

        # (cover) each edge is assigned to exactly one layer
        for e in range(n):
            prob += pulp.lpSum(x[e][k] for k in range(K)) == 1

        # (matching) at most one edge per vertex per layer
        for v, edge_list in vertex_edges.items():
            if len(edge_list) > 1:
                for k in range(K):
                    prob += pulp.lpSum(x[e][k] for e in edge_list) <= 1

        # (precedence) for each Hasse arc (e_pred, e_succ):
        #   Σ_k (k+1)·x[e_succ][k] >= Σ_k (k+1)·x[e_pred][k] + 1
        # Using k+1 (1-indexed) avoids the 0-coefficient problem when e_pred is
        # in layer 0 — a purely 0-indexed formulation would make that constraint
        # trivially satisfiable even with e_succ also in layer 0.
        for e_pred, e_succ in arcs:
            prob += pulp.lpSum((k + 1) * x[e_succ][k] for k in range(K)) >= (
                pulp.lpSum((k + 1) * x[e_pred][k] for k in range(K)) + 1
            )

        # (non-empty) u[k] = 1 whenever any edge occupies layer k
        for k in range(K):
            for e in range(n):
                prob += u[k] >= x[e][k]

        # (no-holes) layers are packed contiguously from the front: u[0] >= u[1] >= ...
        for k in range(K - 1):
            prob += u[k] >= u[k + 1]

        # (label-use) t[s_idx][k] = 1 whenever label s appears in layer k
        for s_idx, s in enumerate(alphabet):
            for e in label_edges.get(s, []):
                for k in range(K):
                    prob += t[s_idx][k] >= x[e][k]

        depth_expr = pulp.lpSum(u[k] for k in range(K))
        pattern_proxy_expr = pulp.lpSum(
            t[s_idx][k] for s_idx in range(len(alphabet)) for k in range(K)
        )

        if objective == "depth":
            if not minimize_secondary:
                prob += depth_expr
            else:
                prob += pattern_proxy_expr
                prob += depth_expr == fixed_primary
        else:  # "pattern"
            if not minimize_secondary:
                prob += pattern_proxy_expr
            else:
                prob += depth_expr
                prob += pattern_proxy_expr == fixed_primary

        prob.solve(solver)

        status = pulp.LpStatus[prob.status]
        if status == "Infeasible":
            raise RuntimeError(
                f"ILP is infeasible for instance with {n} edges and K={K} layers. "
                "This should not happen for a valid StratificationInstance."
            )

        # Extract solution: for each edge, find the layer with x[e][k] > 0.5
        depth_of: dict[int, int] = {}
        for e in range(n):
            for k in range(K):
                val = pulp.value(x[e][k])
                if val is not None and val > 0.5:
                    depth_of[e] = k
                    break

        # Fallback if CBC hit a time limit before finding a feasible solution
        if len(depth_of) < n:
            ordering = instance.linear_extension()
            depth_of = pack_into_layers(instance, ordering)

        # Only report a primary objective value if CBC actually solved to
        # optimality.  If the solver was stopped (e.g. by a time limit) the
        # value coming out of ``pulp.value(...)`` is from the LP relaxation
        # and is not safe to use as a stage-2 fixed-objective constraint —
        # doing so would render stage 2 genuinely infeasible.
        if status == "Optimal":
            if objective == "depth":
                primary_val = pulp.value(depth_expr)
            else:
                primary_val = pulp.value(pattern_proxy_expr)
        else:
            primary_val = None

        return depth_of, primary_val

    # Stage 1: minimise the primary objective
    depth_of, primary_val = _build_and_solve()

    # Stage 2: fix the primary objective at its optimum, then minimise the
    # secondary.  Skipped if stage 1 did not reach optimality, since the
    # fixed-primary constraint would otherwise be derived from a non-integer
    # LP-relaxation value.
    if primary_val is not None:
        depth_of, _ = _build_and_solve(
            fixed_primary=round(primary_val),
            minimize_secondary=True,
        )

    return assignment_to_stratification(instance, depth_of)
