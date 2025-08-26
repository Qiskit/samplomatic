## [0.4.0](https://github.com/Qiskit/samplomatic/tree/0.4.0) - 2025-08-26

### Added

- Added support for measurements after twirled measurements. ([#82](https://github.com/Qiskit/samplomatic/issues/82))


## [0.3.0](https://github.com/Qiskit/samplomatic/tree/0.3.0) - 2025-08-22

### Removed

- Removed `samplomatic.samplex.interfaces.SamplexInput`, just use `samplomatic.tensor_interface.TensorInterface` instead. ([#79](https://github.com/Qiskit/samplomatic/issues/79))

### Added

- Added the `broadcastable` attribute to `TensorSpecification`, with the behaviour that all broadcastable tensor values given to a `TensorInterface` are allowed to be mutually broadcastable. ([#79](https://github.com/Qiskit/samplomatic/issues/79))

### Changed

- Measurement bit-flips included in the output of `Samplex.sample` are now stored per classical register rather than a single array, for example, the former single entry `"measurement_flips"` will now be two entries `"measurement_flips.alpha"` and `"measurement_flips.beta"` if the underlying circuit has two classical registers named `"alpha"` and `"beta"`. ([#78](https://github.com/Qiskit/samplomatic/issues/78))
- Renamed and moved `samplomatic.samplex.interfaces.Interface` to `samplomatic.tensor_interface.TensorInterface`. Likewise moved `Specification` and `TensorSpecification` to `samplomatic.tensor_interface`. Changed `Samplex.inputs()` to return a `TensorSpecification`, populated with what used to be the defaults of `SamplexInput`. ([#79](https://github.com/Qiskit/samplomatic/issues/79))


## [0.2.0](https://github.com/Qiskit/samplomatic/tree/0.2.0) - 2025-08-20

### Added

- Added the `Samplex.inputs()` and `Samplex.outputs()` methods to query the required inputs and promised outputs of `Samplex.sample()`. ([#75](https://github.com/Qiskit/samplomatic/issues/75))

### Changed

- Renamed the parameter `size` to `num_randomizations` in the `Samplex.sample()` method. ([#69](https://github.com/Qiskit/samplomatic/issues/69))
- The `build()` function now calls `Samplex.finalize()` so that it does not need to be called afterwards manually.
  Additionally, the `Samplex.finalize()` method now returns itself for chaining calls. ([#72](https://github.com/Qiskit/samplomatic/issues/72))
- The `Samplex.sample()` method now takes a `SamplexInput` as argument rather than keyword arguments.
  This object can be constructed with the new `Samplex.inputs()` method and only includes arguments pertinent to a given instance of `Samplex`. ([#75](https://github.com/Qiskit/samplomatic/issues/75))


## [0.1.0](https://github.com/Qiskit/samplomatic/tree/0.1.0) - 2025-08-15

### Added

- Initial population of the library with features, including:
   - transpiler passes to aid in the boxing of circuits with annotations
   - the `samplomatic.Samplex` object and all necessary infrastructure to
     describe certain types of basic Pauli randomization and noise injection
   - certain but not comprehensive support for dynamic circuits
   - the `build()` method for interpretting boxed-up circuits into template/samplex pairs ([#38](https://github.com/Qiskit/samplomatic/issues/38))
