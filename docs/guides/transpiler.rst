
Transpiler
==========

The :meth:`samplomatic.transpiler.generate_boxing_pass_manager` is a flexible and convenient function that
builds :class:`qiskit.transpiler.PassManager`\s able to group the circuit instructions into annotated boxes.
Whether you want to automate your workflow, you are interested in trying different boxing strategies for your
circuits, or you simply want a quick and easy alternative to grouping and annotating by hand,
:meth:`samplomatic.transpiler.generate_boxing_pass_manager` has you covered.

This guide illustrates how to use :meth:`samplomatic.transpiler.generate_boxing_pass_manager` and its aguments.
To highlight the effects of each of the function's arguments, in the sections that follow we will mainly target
the circuit below.

.. plot::
   :include-source:
   :context: close-figs

   >>> from qiskit.circuit import QuantumCircuit, Parameter
   >>>
   >>> circuit = QuantumCircuit(4, 7)
   >>> circuit.h(1)
   >>> circuit.h(2)
   >>> circuit.cz(1, 2)
   >>> circuit.h(1)
   >>> circuit.cx(1, 0)
   >>> circuit.cx(2, 3)
   >>> circuit.measure(range(1, 4), range(3))
   >>> circuit.cx(0, 1)
   >>> circuit.cx(1, 2)
   >>> circuit.cx(2, 3)
   >>> for qubit in range(4):
   >>>   circuit.rz(Parameter(f"th_{qubit}"), qubit)
   >>>   circuit.rx(Parameter(f"phi_{qubit}"), qubit)
   >>>   circuit.rz(Parameter(f"lam_{qubit}"), qubit)
   >>> circuit.measure(range(4), range(3, 7))
   >>>
   >>> circuit.draw("mpl", scale=0.8)

Group operations into boxes
---------------------------

The argument ``enable_gates`` can be set to ``True`` or ``False`` to specify whether the two-qubit gates should be grouped into
boxes. Similarly, ``enable_measures`` allows specifying whether or not measurements should be grouped. The following
snippet shows an example where both gates and measurements are grouped.

.. plot::
   :include-source:
   :context: close-figs

   >>> from samplomatic.transpiler import generate_boxing_pass_manager
   >>>
   >>> pm = generate_boxing_pass_manager(
   >>>   enable_gates=True,
   >>>   enable_measures=True,
   >>> )
   >>> transpiled_circuit = pm.run(circuit)
   >>> transpiled_circuit.draw("mpl", scale=0.8)

As can be seen in the figure, the pass manager creates boxes of two types: those that contain a single layer of
two-qubit gates, and those that contain a single layer of measurements. This separation reflects standard practices
in noise learning and mitigation protocols, which usually target layers of homogeneous operations. The two-qubit gates
and measurements are placed in the leftmost box that can accommodate them, and every single-qubit gates is placed in
the same box as the two-qubit gate or measurement they preceed.

The following snippet shows another example where ``enable_gates`` is set to ``False``. As can be seen, the two-qubit
gates are not grouped into boxes, nor are the single-qubit gates that preceed them.

.. plot::
   :include-source:
   :context: close-figs

   >>> pm = generate_boxing_pass_manager(
   >>>   enable_gates=False,
   >>>   enable_measures=True,
   >>> )
   >>> transpiled_circuit = pm.run(circuit)
   >>> transpiled_circuit.draw("mpl", scale=0.8)

Choose how to dress your boxes
------------------------------

All the two-qubit gates and measurement boxes in the returned circuit own left-dressed annotations. In particular,
all the boxes that contain two-qubit gates are annotated with a :class:`.~Twirl`, while for measurement boxes, users can
choose between :class:`.~Twirl`, :class:`.~BasisTranform` (with ``mode="measure"``), or both. The following code
generates a circuit where the all the boxes are twirled, and the measurement boxes are additionally annotated with
:class:`.~BasisTranform`.

.. plot::
   :include-source:
   :context: close-figs

   >>> pm = generate_boxing_pass_manager(
   >>>   enable_gates=True,
   >>>   enable_measures=True,
   >>>   measure_annotations="all",
   >>> )
   >>> transpiled_circuit = pm.run(circuit)

Prepare your circuit for noise injection
----------------------------------------

The ``inject_noise_targets`` allows specifying what boxes should receive an :class:`.~InjectNoise` annotation. As an example,
the following snippet generates a circuit where the two-qubit gates boxes own an :class:`.~InjectNoise` annotation but the
measurement boxes do not.

.. plot::
   :include-source:
   :context: close-figs

   >>> pm = generate_boxing_pass_manager(
   >>>   enable_gates=True,
   >>>   enable_measures=True,
   >>>   inject_noise_targets="gates",
   >>> )
   >>> transpiled_circuit = pm.run(circuit)

If a circuit contains two or more boxes that are equivalent up to one-qubit gates, all of them are annotated with
an :class:`.~InjectNoise` annotation with the same ``ref``. Thus, the number of unique ``InjectNoise.ref``\s in the returned
circuit is equal to the number of unique boxes (where uniqueness is defined up to one-qubit gates).

By selecting the appropriate value for ``inject_noise_strategy``, users can decide whether the :class:`.~InjectNoise` annotations
should have:

* ``modifier_ref=''``, recommended when modifying the noise maps prior to sampling from them is not required,
* ``modifier_ref=ref``, recommended when all the noise maps need to be scaled uniformly by the same factor, or
* a unique value of ``modifier_ref``, recommended when every noise map needs to be scaled by a different factor.

The following code generates a circuit where the two-qubit gates boxes own an :class:`.~InjectNoise` annotation with unique
values of ``modifier_ref``.

.. plot::
   :include-source:
   :context: close-figs

   >>> pm = generate_boxing_pass_manager(
   >>>   enable_gates=True,
   >>>   enable_measures=True,
   >>>   inject_noise_targets="gates",
   >>>   inject_noise_strategy="individual_modification",
   >>> )
   >>> transpiled_circuit = pm.run(circuit)

Specify how to treat barriers
-----------------------------

By default, barriers are removed from the circuit prior to grouping the operations, as shown in the following
snippet.

.. plot::
   :include-source:
   :context: close-figs

   >>> circuit_with_barrier = QuantumCircuit(4)
   >>> circuit_with_barrier.cz(0, 1)
   >>> circuit_with_barrier.barrier()
   >>> circuit_with_barrier.cz(2, 3)
   >>> circuit_with_barrier.measure_all()
   >>>
   >>> pm = generate_boxing_pass_manager()
   >>> transpiled_circuit = pm.run(circuit_with_barrier)
   >>> transpiled_circuit.draw("mpl", scale=0.8)

Setting ``remove_barriers`` to ``False`` allows preserving the barriers.

.. plot::
   :include-source:
   :context: close-figs

   >>> pm = generate_boxing_pass_manager(
   >>>   remove_barriers=False,
   >>> )
   >>>
   >>> transpiled_circuit = pm.run(circuit_with_barrier)
   >>> transpiled_circuit.draw("mpl", scale=0.8)

Notice that when two gates are separated by a barrier, setting ``remove_barriers`` to ``True`` potentially
allows them to be placed into the same box. However, if ``remove_barriers`` is set to ``False``, they are
sure to be placed into different boxes. Thus, choosing to preserve the barriers guarantees that the
alignment and schedule of gates in the input circuit are respected, but it generally results in circuits
with larger depths.

Build your circuit
------------------

Every pass manager produced by :meth:`samplomatic.transpiler.generate_boxing_pass_manager` returns
circuits that can be successfully turned into a template/samplex pair by :meth:`samplomatic.build`. As an
example, the following code calls the :meth:`samplomatic.build` function on a circuit produced by a boxing pass
manager.

.. plot::
   :include-source:
   :context: close-figs

   >>> from samplomatic import build
   >>>
   >>> pm = generate_boxing_pass_manager(
   >>>   enable_gates=True,
   >>>   enable_measures=True,
   >>> )
   >>> transpiled_circuit = pm.run(circuit)
   >>>
   >>> template, samplex = build(transpiled_circuit)

In order to ensure that any transpiled circuit can be successfully built, the pass managers know how to
include additional boxes when they are needed. As an example, consider the circuit below, which ends with an
unmeasured qubit.

.. plot::
   :include-source:
   :context: close-figs

   >>> circuit_with_unmeasured_qubit = QuantumCircuit(4, 3)
   >>> circuit_with_unmeasured_qubit.cz(0, 1)
   >>> circuit_with_unmeasured_qubit.cz(2, 3)
   >>> for qubit in range(4):
   >>>   circuit_with_unmeasured_qubit.rz(Parameter(f"th_{qubit}"), qubit)
   >>>   circuit_with_unmeasured_qubit.rx(Parameter(f"phi_{qubit}"), qubit)
   >>>   circuit_with_unmeasured_qubit.rz(Parameter(f"lam_{qubit}"), qubit)
   >>> circuit_with_unmeasured_qubit.measure(range(1, 4), range(3))
   >>>
   >>> circuit_with_unmeasured_qubit.draw("mpl", scale=0.8)

Drawing left-dressed boxes around the gates and the measurements would result in a circuit that has uncollected
virtual gates on qubit ``0``, and calling :meth:`samplomatic.build` on this circuit would result in an error. To
avoid this, the pass managers returned by :meth:`samplomatic.transpiler.generate_boxing_pass_manager` are allowed
to add right-dressed boxes to act as collectors. As an example, in the following snippet qubit ``0`` is
terminated by a right-dressed box that picks up the uncollected virtual gate. The single-qubit gates acting on qubit
``0`` are also placed inside the box, in order to minimise the depth of the resulting circuit.

.. plot::
   :include-source:
   :context: close-figs

   >>> pm = generate_boxing_pass_manager(
   >>>   enable_gates=True,
   >>>   enable_measures=True,
   >>> )
   >>> transpiled_circuit = pm.run(circuit_with_unmeasured_qubit)
   >>> transpiled_circuit.draw("mpl", scale=0.8)

In another example, a right-dressed box is added to collect the virtual gates that would otherwise remain
uncollected due to the unboxed measurements.

.. plot::
   :include-source:
   :context: close-figs

   >>> pm = generate_boxing_pass_manager(
   >>>   enable_gates=True,
   >>>   enable_measures=False,
   >>> )
   >>> transpiled_circuit = pm.run(circuit_with_unmeasured_qubit)
   >>> transpiled_circuit.draw("mpl", scale=0.8)
