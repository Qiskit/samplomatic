A *hypergraph* is a pair `H = (Q, E)` in
which `Q` is a finite vertex set and `E` is a multiset of non-empty
subsets of `Q`. The case in which every edge has size two
recovers ordinary multigraphs. A *partial order* on a set is a
reflexive, antisymmetric, transitive relation. Within such an order, a
*chain* is a totally ordered subset and an *antichain* is a subset of
pairwise incomparable elements. Finally, a *strong matching* in `H` is
a set of pairwise vertex-disjoint edges.

With these pieces in hand, fix a hypergraph `H = (Q, E)`, a partial
order `≺` on `E`, and a labelling `σ : E → Σ`. A *layer* `L ⊆ E` is an
antichain in `≺` that is also a strong matching, and its *pattern* is
the label set `pat(L) = {σ(e) : e ∈ L} ⊆ Σ`.
The need for labels and patterns is made clear in the next section.
A *stratification* is a
sequence `L_1, …, L_m` of layers that are pairwise disjoint, that cover
`E`, and whose order is consistent with `≺`. Two integers are
associated with such a sequence:

- the *depth* `m`, and
- the *unique-pattern count* `|Λ| = |{pat(L_1), …, pat(L_m)}|`.

Both quantities are to be minimized. Different downstream consumers
weight them differently: some prefer the smallest possible `m` and
treat `|Λ|` as a tiebreaker, while others prefer the smallest possible
`|Λ|` and treat `m` as a tiebreaker. The algorithms below cover the
spectrum.

## Quantum circuits as instances

Every quantum circuit on a qubit set `Q` induces an instance of the
problem. Suppose the circuit's instruction types have been divided into
"easy" instructions (typically single-qubit gates) and "hard"
instructions (typically multi-qubit gates and measurements). The
instance is then defined as follows:

- the vertex set is `Q`;
- the edge multiset `E` contains one edge per hard instruction, equal
  to that instruction's qubit support;
- the labelling is `σ(g) = (name(g), canon(qargs(g)))`, where `canon`
  returns the canonical qubit tuple under the instruction's
  port-symmetry group — the unordered pair for symmetric gates such as
  `cz`, `rzz`, and `swap`, and the ordered pair for asymmetric gates
  such as `cx`.

Easy instructions do not appear in `E` and play no role in the layer
analysis. Once a stratification has been chosen, they are slotted into
their own layers, interleaved with `L_1, …, L_m` .

The partial order `≺` is the *commutation-respecting precedence* on
`E`: we set `g ≺ g'` iff every total order on `E` that realises the
circuit's unitary places `g` before `g'`. Equivalently, the antichains
of `≺` are precisely the sets of gates that may be reordered without
changing the action of the circuit. Three phenomena contribute to
incomparability: disjoint qubit support, commutation across a shared
qubit, and multi-qubit commutation such as `[X⊗X, Z⊗Z] = 0`.

Computing `≺` exactly may be intractable depending on the complexity
of present instructions, but any partial order
`≺' ⊇ ≺` that still respects the unitary is admissible.

Minimising `|Λ|` is motivated by the noise-learning use case: each distinct
pattern corresponds to one layer-based noise-characterisation experiment, and
such experiments are expensive.  Because qubits are not fungible — the noise
channel of a gate depends on which physical qubits it acts on — the label `σ`
encodes the specific qubit support of each gate (not merely its gate type), so
that two layers with different physical placements are correctly counted as
distinct patterns requiring separate experiments.

## Complexity remarks

Even with `σ` constant (so `|Λ|` is degenerate), minimizing `m` is a
precedence-constrained edge-coloring problem and is NP-hard in
general; it reduces to ordinary edge coloring when `≺` is empty and to
list-scheduling on a DAG when every edge has size one. Adding the
second objective `|Λ|` cannot make the problem easier. Consequently,
practical algorithms are heuristics with provable structural
guarantees, and an exact integer-program is included as a baseline.

Throughout, `pred(e) = {e' ∈ E : e' ≺ e}` and a *ready* edge is one
all of whose predecessors have already been placed. Two edges
*conflict* if they share a vertex of `Q`. A layer being valid means
its members are pairwise non-conflicting and pairwise incomparable in
`≺`; the latter holds automatically once we always place ready edges.

## Algorithm A — Greedy list scheduling (depth-first)

Intuition. Walk `E` in any linear extension of `≺` and pack each edge
into the earliest already-open layer where it does not conflict, or
start a new layer. Patterns are ignored entirely. This is the
classical layered scheduler; it is fast and yields the optimal `m`
when the conflict structure is interval-like, and is otherwise within
a constant factor of optimal.

```
Input:  H = (Q, E), partial order ≺
Output: layers L_1, …, L_m

1.  topo ← any linear extension of ≺
2.  layers ← [] ; depth_of ← {}
3.  for e in topo:
4.      d_min ← 1 + max(depth_of[e'] for e' in pred(e), default = 0)
5.      k ← smallest index ≥ d_min such that
            (k > |layers|) or (vertices(e) ∩ vertices(L_k) = ∅)
6.      if k > |layers|: append empty L_k to layers
7.      L_k ← L_k ∪ {e} ; depth_of[e] ← k
8.  return layers
```

Cost is `O(|E| · m · max_e |e|)`. Output is a valid stratification by
construction.

## Algorithm B — Coffman–Graham with pattern tiebreaker (depth-first, `|Λ|` as tiebreaker)

Intuition. Replace the arbitrary linear extension of A with a priority
order that schedules edges on long chains first; among layers that are
feasible for an edge `e`, prefer the one whose current pattern
already contains `σ(e)` so that adding `e` does not enlarge `pat(L_k)`.
This keeps `m` close to the Coffman–Graham bound while opportunistically
shrinking `|Λ|`.

```
Input:  H = (Q, E), partial order ≺, labelling σ
Output: layers L_1, …, L_m

1.  for each e in E:
2.      h(e) ← longest chain length from e to any sink in ≺
3.  prio ← edges sorted by (h(e) descending, |e| descending, id)
4.  layers ← [] ; depth_of ← {}
5.  for e in prio (re-sorted as edges become ready):
6.      d_min ← 1 + max(depth_of[e'] for e' in pred(e), default = 0)
7.      candidates ← {k ≥ d_min :
                       k > |layers| or vertices(e) ∩ vertices(L_k) = ∅}
8.      partition candidates into:
            reuse ← {k : σ(e) ∈ pat(L_k)}
            grow  ← candidates \ reuse
9.      if reuse non-empty: k ← min(reuse)
        else:               k ← min(grow)
10.     if k > |layers|: append empty L_k
11.     L_k ← L_k ∪ {e} ; depth_of[e] ← k
12. return layers
```

Cost is `O(|E| · (m + log |E|))`. The `reuse` preference is purely
local but in practice eliminates many singleton patterns produced by A.


## Algorithm E — Pattern-bucketed batch scheduling (pattern-first, depth-aware)

Intuition. Like D, every emitted layer remains monochromatic, so
`|Λ| ≤ |Σ|` still holds, but the choice of *which* label to emit next
is data-driven: pick the label whose currently-extractable matching
is largest, breaking ties toward labels with more remaining work.
This trades a little of D's strict label ordering for noticeably
smaller `m`.

```
Input:  H, ≺, σ
Output: layers L_1, …, L_m, each monochromatic

1.  remaining ← E ; layers ← []
2.  while remaining is non-empty:
3.      ready ← {e ∈ remaining : pred(e) ⊆ placed}
4.      for each label s with ready edges:
5.          M_s ← maximal strong matching in {e ∈ ready : σ(e) = s}
6.      s* ← argmax_s |M_s|, ties → label with most remaining edges
7.      emit layer M_{s*} ; remove from remaining
8.  return layers
```

This is essentially a 1-step lookahead version of D. The matchings
are recomputed every round, but only over `ready` edges, and modern
incremental matching keeps the per-round cost near linear in `|ready|`.

## Algorithm F — Lexicographic ILP (exact, either ordering)

Intuition. For a reference solution against which the heuristics can
be benchmarked. Encode layer assignment, pattern usage, and the depth
indicator, then minimize lexicographically in the user's preferred
order.

Variables (with `K` an upper bound on `m`, e.g. the output of A):

- `x_{e,k} ∈ {0, 1}` — edge `e` placed in layer `k`, for `k ∈ {1,…,K}`.
- `u_k    ∈ {0, 1}` — layer `k` is non-empty.
- `y_{P,k}∈ {0, 1}` — layer `k` realises pattern `P ⊆ Σ`.
- `z_P    ∈ {0, 1}` — pattern `P` is used somewhere.

Constraints:

```
(cover)        Σ_k x_{e,k} = 1                          ∀ e ∈ E
(precedence)   Σ_k k · x_{e,k} < Σ_k k · x_{e',k}        ∀ e ≺ e'
(matching)     Σ_{e ∋ q} x_{e,k} ≤ 1                    ∀ q ∈ Q, k
(non-empty)    u_k ≥ x_{e,k}                            ∀ e, k
(pattern-link) y_{σ(e), in pattern P, k} bookkeeping    (standard ind.)
(pattern-used) z_P ≥ y_{P,k}                            ∀ P, k
```

Objectives:

- Depth         `m̂  = Σ_k u_k`
- Pattern count `Λ̂  = Σ_P z_P`

Solve in two stages, in the user-chosen order:

```
Depth-first:
  m*  = min m̂
  Λ*  = min Λ̂   subject to  m̂ = m*

Pattern-first:
  Λ*  = min Λ̂
  m*  = min m̂   subject to  Λ̂ = Λ*
```

Strict precedence is encoded with the standard `+1` slack on integer
layer indices. The pattern-link constraints are the standard product
linearisation of `y_{P,k} = ∏_{s∈P} [s ∈ pat(L_k)] · ∏_{s∉P} [s ∉ pat(L_k)]`.

## Algorithm G — GRASP-style randomized multi-start (stochastic, either ordering)

Intuition. Algorithms A and B each commit to a single argmax at every
step and so explore exactly one trajectory. GRASP (greedy randomized
adaptive search procedure) wraps either of them in a multi-start loop
in which the *edge-selection* step samples uniformly from the top-`α`
candidates instead of taking the strict argmax. Across `r` restarts
the construction visits a diverse set of feasible stratifications; the
best one under the user's `key` is kept. The parameter
`α ∈ [0, 1]` interpolates between fully greedy (`α = 0`, recovers the
underlying deterministic algorithm) and fully random (`α = 1`).

```
Input:  H, ≺, σ, base ∈ {A, B},
        restart count r, restricted-candidate ratio α ∈ [0, 1],
        preference key(L) ∈ {(m,|Λ|), (|Λ|,m)}
Output: layers L_1, …, L_m

1.  best ← None
2.  for trial = 1, …, r:
3.      run base, but at the edge-selection step:
4.          score each ready edge e by chain_height(e)
5.          let s_max, s_min be the best/worst scores in ready set
6.          threshold τ ← s_max − α · (s_max − s_min)
7.          RCL ← {e ∈ ready : chain_height(e) ≥ τ}
8.          choose e uniformly at random from RCL
9.          then apply the base's layer-selection policy deterministically
10.     L_trial ← resulting stratification
11.     if best is None or key(L_trial) < key(best):
12.         best ← L_trial
13. return best
```

For base B the layer-selection policy (reuse preferred, else earliest
grow) is applied deterministically after the randomized edge draw,
so the pattern-reuse benefit of B is preserved in every trial.

Cost is `r` times the base cost, fully parallel across trials.
Empirically `r ∈ [10, 100]` and `α ∈ [0.1, 0.3]` suffice to close most
of the gap to the ILP on instances of practical size, with the bonus
that the variance across trials is itself a useful diagnostic — small
spread suggests the deterministic base was already near-optimal.

## Local-search refinement

Any of A–E can be post-processed to improve whichever metric matters
most. Three move types suffice:

- **Relocate**: move a single edge `e` from `L_k` to `L_{k'}` provided
  `d_min(e) ≤ k' ≤ d_max(e)` and `L_{k'} ∪ {e}` remains a strong
  matching.
- **Swap**: exchange edges `e ∈ L_k`, `e' ∈ L_{k'}` if both layers
  remain valid and both edges remain within their slack windows.
- **Merge**: replace `L_k, L_{k+1}` by `L_k ∪ L_{k+1}` if the union is
  a strong matching (this drops `m` by one).

Acceptance rule (lexicographic, with the user's preferred ordering):

```
let key(L) = (m, |Λ|)         if depth-first preference
           = (|Λ|, m)         if pattern-first preference
accept move iff key(L_after) < key(L_before)
```

A simple steepest-descent loop suffices in most cases; if the
neighborhood plateau is wide, simulated annealing on `key`
lexicographic-distance gives further reduction at extra cost.

## Summary

| Algorithm | Optimizes first | Secondary | `m` quality       | `|Λ|` quality       | Cost              | Exact? |
|-----------|-----------------|-----------|-------------------|---------------------|-------------------|--------|
| A         | `m`             | —         | optimal           | none                | `O(|E| m)`        | no     |
| B         | `m`             | `|Λ|`     | optimal           | local reuse         | `O(|E|(m+log|E|))`| no     |
| E         | `|Λ|`           | `m`       | moderate          | `≤ |Σ|` exact bound | per-round matching| no     |
| F         | user-chosen     | the other | optimal           | optimal†            | exponential worst | yes†   |
| G         | user-chosen     | the other | best of `r` runs  | best of `r` runs    | `r` × base cost   | no (stochastic) |
| Refine    | user-chosen     | other     | improves any seed | improves any seed   | polynomial / move | no     |

†Algorithm F minimises depth exactly. For the pattern objective it minimises a linear
proxy (total label-uses across layers) that strongly correlates with `|Λ|` but is not
identical to it; apply Refine afterwards for further exact reduction.
