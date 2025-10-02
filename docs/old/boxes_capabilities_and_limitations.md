# Boxes Capabilities and Limitations (As expected in V0.5.0)
This note describes the basic ingredients of Samplomatic, and how they can and can't be used.

## Basic Ingredients
To twirl a Qiskit `QuantumCircuit` one uses boxes. The box specifications define how virtual gates are both emitted and collected. The collection is defined by the dressing of the box - its location relative to the box (left or right) and its decomposition (for example, `RzSx` or `RzRx`). The collector collects the virtual gates, and also greedily absorbs all 1Q gates inside the box (such that these gates are not present at the template circuit).

The emission location is also dictated by the dressing - for a right dressed box, the emitter is added on the left of the box. For a left dressed box, the emitter is added to the right of all gates in the box, but to the left of measurements (if any). Currently, only `Pauli` twirling is supported. In the future, we plan to support more twirl types, including multi-qubit ones, and thus think of the atomic unit in terms of subsystems and not qubits (where the dimension of a single subsystem is given by the qubit count of the twirling).

## Box makeup
Not everything can fit inside a box.

**For Right dressed box**:
- No measurements allowed.
- Entanglers must be on the left of all 1Q gates (on the same qubits).
- Classical `IfElseOp`s must be on the right of all gates involving qubits in the `IfElseOp`.

**For left dressed box**:
- A single measurement per qubit is allowed, provided that it is not followed by any gates on the same qubit.
- Entanglers must be on the right of all 1Q gates (on the same qubits).
- Classical `IfElseOp`s must be on the left of all gates involving qubits in the `IfElseOp`.
- If measurements are included, only `Pauli` twirling is allowed.

In both cases, the gates inside each branch of a classical conditional must respect the ordering restrictions of the respective box, and each qubit can be in at most one `IfElseOp` per box.

A few examples are given in the figure below.

![Box makeup examples](figs/boxes-examples-screenshot.png)



## Box chains
With a single exception, boxes can not function on their own. Only a chain of boxes creates a valid structure where all virtual gates can be safely collected. In this context a chain is not the lexical progression of boxes in the circuit, but rather the boxes involved with a given subsystem. Therefore, each subsystem has its own (in principle, independent) chain. Each chain:
- Must begin with a left dressed box.
- Must be terminated by either a right dressed box, or a left dressed box with measurements.

Following this, the possible chains fall into one of three categories:
- A series of left-dressed boxes with no measurements, followed by a right-dressed box.
- A series of left-dressed boxes with no measurements, followed by a left-dressed box with measurements.
- A single-box chain of left-dressed box with measurements.

A few notes:
- A circuit can contain any number of box chains, as long as they are all valid.
- An empty box with no-ops can be used to start or end a chain when necessary.
- Right-dressed boxes terminate the chains of all subsystems inside them (including no-ops), but left-dressed boxes with measurements terminate the chains only of measured qubits.
- Measurements outside of boxes interfere with the chains, and are not allowed in the middle of a chain.
- Classical conditions outside of boxes interfere with the chains, and are not allowed in the middle of a chain.
- Non-clifford gates outside of boxes interfere with the chains, and are not allowed in the middle of a chain. We expect to lift this restriction in the future.
- A non-twirled measurement cannot follow a left-dressed box with measurement on the same qubit. This behavior might change in the future, and in the meantime could be circumvented by adding an empty chain composed of a left-dressed box followed by a right-dressed box containing no-ops on the necessary qubits.
