from samplomatic import build, Twirl
from qiskit import QuantumCircuit
# >>>
circuit = QuantumCircuit(2)
with circuit.box([Twirl()]):
   circuit.cz(0, 1)
with circuit.box([Twirl()]):
    circuit.measure_all()
# >>>
template, samplex = build(circuit)
samplex.draw() # doctest: +SKIP
