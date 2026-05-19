# Measure-Twirl Branch Status

## Goal

Make measurements act as propagators in dressed boxes: a virtual Pauli entering a measurement has its X component propagated classically (Z2 measurement flip) and quantumly (continued Pauli with randomized Z phase).

## What's Implemented

### New Infrastructure (working, unit tests pass)

1. **Z2->Pauli conversion** (`samplomatic/virtual_registers/z2_register.py`)
   - Added `VirtualType.PAULI` to `CONVERTABLE_TYPES`
   - `convert_to(PAULI)`: `left_shift(array, 1)` maps Z2 `{0,1}` to Pauli `{I=0, X=2}`

2. **PreMeasurePropagate node** (`samplomatic/pre_samplex/graph_data.py`)
   - Dataclass with `creg_name`, `creg_offset`, `direction=Direction.RIGHT`
   - Exported from `pre_samplex/__init__.py`

3. **add_measure_propagate()** (`samplomatic/pre_samplex/pre_samplex.py`)
   - Finds rightward danglers `(PreEmit, PrePropagate, PreMeasurePropagate)`
   - Creates PreMeasurePropagate node, connects predecessors
   - Marks output as OPTIONAL dangler (can be consumed by subsequent gates/collectors)
   - Tracks twirled clbits for duplicate detection

4. **Lowering** (`samplomatic/pre_samplex/pre_samplex.py:add_measure_propagate_nodes`)
   - Fork A: Pauli->Z2 conversion -> CollectZ2ToOutputNode (measurement flip at `creg_offset`)
   - Fork B: Pauli->Z2->Pauli (extract X) + DistributionSamplingNode (random Z) -> CombineRegistersNode
   - Edge between forks ensures correct register lifetime ordering

5. **Serialization fix** (`samplomatic/serialization/node_serializers.py`)
   - `ConversionNodeSerializer.serialize`: `num_subsystems` now stringified for rustworkx JSON

6. **Box builder changes** (`samplomatic/builders/box_builder.py`)
   - `_resolve_clbit()` helper on base BoxBuilder
   - `_validate_twirl_supports_measurement()` — ensures Pauli-compatible twirl type
   - LeftBoxBuilder: twirl emitted at `parse(None)` with `skip_leftward=True`, measurements call `add_measure_propagate` directly in `parse()`, leftward edges connected in `rhs()` via `connect_emit_leftward()`
   - RightBoxBuilder: measurements call `add_measure_propagate` directly in `parse()`
   - `_emit_twirl` returns node indices for deferred leftward connection

7. **PreSamplex API additions**
   - `add_emit_twirl(..., skip_leftward=True)` — creates node + rightward dangler, defers leftward edges
   - `connect_emit_leftward(node_idx)` — adds leftward edges to existing emit node
   - `_connect_emit_leftward()` — shared implementation for leftward edge logic

## The Blocking Problem

Moving the twirl's rightward dangler to `parse(None)` (before hard gates) causes hard gates' `add_propagate` to consume it via rightward propagation. This changes the graph semantics:

- **Original** (twirl at `rhs()`): Hard gates have NO rightward propagation (no dangler exists when they're parsed). The twirl's rightward output exits the box **unpropagated** to the next collector.
- **Current** (twirl at `parse(None)`): Hard gates DO create rightward propagation (consuming the twirl's rightward dangler). The twirl's rightward output exits the box **propagated through hard gates**.

These produce different samplex outputs. The right box's collector receives different inputs, breaking fidelity (52 integration test failures, 854 unit tests pass).

## The Fundamental Tension

- **Measurements need** the twirl's rightward dangler to exist during `parse()` (after `None`, where hard gates and measurements are parsed)
- **Hard gates should NOT** consume the rightward dangler for rightward propagation — they should only create leftward propagation nodes (for the adjacent right box's use)
- **Hard gates currently always consume** any rightward dangler they find via `add_propagate`

## Possible Approaches Forward

### A. Selective rightward propagation in add_propagate
Add a mechanism so hard gates skip rightward PreEmit danglers but still find rightward PrePropagate/PreMeasurePropagate danglers. This way:
- The twirl's PreEmit rightward dangler stays unconsumed by hard gates
- Measurements (which call `add_measure_propagate` directly) CAN find it
- After measurements consume it, subsequent hard gates find PreMeasurePropagate (which they CAN propagate through)

Implementation: split the rightward match in `add_propagate` to only find REQUIRED PreEmit danglers, and mark the twirl's rightward dangler as OPTIONAL. Hard gates skip it; `add_measure_propagate` finds both types.

**Risk**: This changes the semantics for RightBoxBuilder where hard gates DO need to consume the twirl's rightward dangler. Would need the RightBoxBuilder to emit with REQUIRED (default) and LeftBoxBuilder with OPTIONAL.

### B. Separate the measurement path entirely
Don't move the twirl to `parse(None)`. Instead, keep the twirl at `rhs()` and have `add_measure_propagate` work retroactively — it finds the measurement's qubit in the emission created by `rhs()` and splices in the measurement propagation after the fact.

### C. Two-phase rightward dangler
Create the rightward dangler at `parse(None)` but in a "measurement-only" state that hard gates' `add_propagate` ignores. After all hard gates and measurements have been parsed, in `rhs()`, if any rightward dangler remains (measurements didn't consume all qubits), promote the unconsumed portion to a normal dangler for the next collector.

## Test Status

- **854 unit tests**: all pass
- **52 integration tests**: fail (fidelity drops to ~0.03, characteristic of random unitary)
- **1190 integration tests**: pass
- Failures are in `test_static_twirling_samples.py` (44) and `test_change_basis_samples.py` (8) — all cases with hard gates in left-dressed boxes
