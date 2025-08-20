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
