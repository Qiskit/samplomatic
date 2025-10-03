
Transpiler
==========

The :meth:`samplomatic.transpiler.generate_boxing_pass_manager` is designed to provide a flexible and convenient
way of grouping the operations of a circuit into annotated boxes. Whether you want to automate your workflow, you
are interested in trying different boxing strategies for your circuits, or you simply want a quick and easy
alternative to grouping and annotating by hand, the :meth:`samplomatic.transpiler.generate_boxing_pass_manager`
has you covered.

This guide illustrates how to use :meth:`samplomatic.transpiler.generate_boxing_pass_manager` to box up quantum
circuits. To highlight the effects of each of the function's arguments, we will mainly target the following circuit,
which contains single- and two-qubit gates as well as mid-circuit and terminal measurements.

.. plot::
   :include-source:
   :context: close-figs

   >>> from qiskit.circuit import QuantumCircuit, Parameter
   >>>
   >>> circuit = QuantumCircuit(4, 4)
   >>> circuit.h(1)
   >>> circuit.h(2)
   >>> circuit.cz(1, 2)
   >>> circuit.h(1)
   >>> circuit.cx(1, 0)
   >>> circuit.cx(2, 3)
   >>> circuit.measure(range(1, 4), range(1, 4))
   >>> circuit.cx(0, 1)
   >>> circuit.cx(1, 2)
   >>> circuit.cx(2, 3)
   >>> for qubit in range(4):
   >>>   circuit.rz(Parameter(f"th_{qubit}"), qubit)
   >>>   circuit.rx(Parameter(f"phi_{qubit}"), qubit)
   >>>   circuit.rz(Parameter(f"lam_{qubit}"), qubit)
   >>> circuit.measure(range(4), range(4))
   >>>
   >>> circuit.draw("mpl", scale=0.8)

Grouping operations into boxes
------------------------------

The argument ``enable_gates`` can be set to ``True`` or ``False`` to specify whether the two-qubit gates should be grouped into
boxes. Similarly, ``enable_measure`` allows specifying whether or not measurements should be grouped. The following
snippet shows an example where both gates and measurements are grouped.

.. plot::
   :include-source:
   :context: close-figs

   >>> from samplomatic.transpiler import generate_boxing_pass_manager
   >>>
   >>> pm = generate_boxing_pass_manager(
   >>>   enable_gates=True,
   >>>   enable_measure=True,
   >>> )
   >>> transpiled_circuit = pm.run(circuit)
   >>> transpiled_circuit.draw("mpl", scale=0.8)

As can be seen in the figure, the pass manager creates boxes of two types: those that contain a single layer of
two-qubit gates, and those that contain a single layer of measurements. This separation reflects standard practices
in noise learning and mitigation protocols, which usually target layers of homogeneous operations. The two-qubit gates
and measurements are placed in the leftmost box that can accommodate them, and every single-qubit gates is placed in
the same box as the two-qubit gate or measurement they preceed.

By default, the barrier is removed from the circuit prior to grouping the operations, but setting ``remove_barriers``
to ``False`` preserves it.

.. plot::
   :include-source:
   :context: close-figs

   >>> from samplomatic.transpiler import generate_boxing_pass_manager
   >>>
   >>> pm = generate_boxing_pass_manager(
   >>>   enable_gates=True,
   >>>   enable_measure=True,
   >>>   remove_barriers=False,
   >>> )
   >>> transpiled_circuit = pm.run(circuit)
   >>> transpiled_circuit.draw("mpl", scale=0.8)

The following snippet shows an example where ``enable_measure`` is set to ``False``. As can be seen, the measurements
are not grouped into boxes, nor are the single-qubit gates that preceed them.

.. plot::
   :include-source:
   :context: close-figs

   >>> from samplomatic.transpiler import generate_boxing_pass_manager
   >>>
   >>> pm = generate_boxing_pass_manager(
   >>>   enable_gates=True,
   >>>   enable_measure=False,
   >>>   remove_barriers=False,
   >>> )
   >>> transpiled_circuit = pm.run(circuit)
   >>> transpiled_circuit.draw("mpl", scale=0.8)

Annotating boxes
----------------

When ``enable_gates`` is ``True``, by default every box containing two-qubit gates is annotated with a

.. plot::
   :include-source:
   :context: close-figs

   >>> from samplomatic.transpiler import generate_boxing_pass_manager
   >>>
   >>> pm = generate_boxing_pass_manager(
   >>>   enable_gates=True,
   >>>   enable_measure=False,
   >>> )
   >>> transpiled_circuit = pm.run(circuit)
   >>> print(transpiled_circuit[0])
