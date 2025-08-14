![Samplomatic](../assets/samplomatic.svg)

## Introduction

Samplomatic is a library that helps you sample randomizations of your quantum circuits in exactly the way that you specify.
Pauli twirling a static circuit will be the first milestone, but the possible types of sampling will be extensible by design—we hope that you will contribute your own weird groups!
This library will also not be specific to twirling, though a primary use-case, it will also support ideas like sample-based noise injection, as used in PEC.

## Circuit Ensembles

### Twirling and Sampling

Twirling and other circuit sampling processes are a common requirement when executing on noisy quantum hardware.

At a high level, twirling is a process of taking a fixed, base circuit and using it to create a distribution over circuits
that are structurally similar (in the sense of scheduling) to the base circuit.
Variates of the distribution are drawn and executed on hardware.
Group and representation theoretic ideas are used to derive the specifics about how the distribution should be formed, and in
such a way that the experimental results from these variates, when pooled, somehow have a more favorable noise profile.

![Twirling Ensembles](figs/twirling-ensembles.png)

The canonical example is Pauli twirling a stratified circuit.
Each layer of a circuit is surrounded by random Pauli gates in such a way that the logical action of the base circuit is unchanged.
This has the effect of turning each layer's noise channel into a Pauli channel.
Pauli channels are stochastic, so that noise accumulates more predictably, and is also easier to reason about in general.

![Pauli Twirling](figs/pauli-twirling-screenshot.png)

Another example used by some error mitigation strategies, like PEC and PEA, is the intentional injection of Pauli noise into each layer of a circuit.

![Pauli Twirling](figs/pea-utility-screenshot.png)


### What IBM Hardware is Good At

IBM has optimized the control electronics and stack above it to be very good at compiling parametric circuits and executing them many times. Conversely, and naturally because of compilation overhead, it is less efficient at executing many distinct circuits.
Below is some pseudo-code showing what the execution pipeline looks like.

```python
# connect to hardware
qcf_client = VirtualQCFClient(<...>)

# request that 3 parametric circuits be compiled
compile_request = qcf_client.compile([circuit1, circuit1, circuit3], shots=64)
module = qcf_client.get_module(compile_request)

# execute the module with many different parameter sets
for idx in range(1000:)
    execute_request = qcf_client.execute(module, [<params0_idx>, <params1_idx>, <params2_idx>])
```

### Parameter Ensembles

Given that our hardware is good at executing the same parametric circuits with many distinct parameter values sets, but not as much at executing many distinct circuits, it is natural to rephrase the problem in this way.
To this end

![Parameter Ensembles](figs/parameter-ensembles.drawio.png)

## Boxes and Annotations: declarative twirling and sampling

## Virtual Gates

Virtual Z gates are directives to modify the quadrature phase of all subsequent pulses on a control line.
Equivalently, but less practically, they could be directives to decrement the quadrature phase of all preceding pulses on a control line.
Equivalently, but also less practically, they could split the difference between the future and past.

![Virtual Z Gates](figs/virtual-z.drawio.png)

The point is that virtual Z gates are not so much gates as directives that other pieces of the circuit should be implemented differently, and in such a way that some gate `Z(a)` is implemented "virtually".

We can extend this notion of virtual Z gates to more broad sets of unitary action.
We call these virtual gates.
Virtual gates can be pictured to live on the circuit wires of a circuit diagram, where they are not intended to, alone, be physically implemented.
Rather, they are directives to modify the implementation of some other circuit component(s).

![Virtual Z Gates](figs/virtual-gates.drawio.png)

## Samplexes

![Samplex](figs/toy-samplex-construction.drawio.png)
