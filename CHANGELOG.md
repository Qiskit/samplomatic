## [0.9.0](https://github.com/Qiskit/samplomatic/tree/0.9.0) - 2025-09-30

### Added

- Added the `targets` input to the `AddInjectNoise` pass to specify boxes to add an `InjectNoise` annotation to.
- Added the `inject_noise_targets` input to `generate_boxing_pass_manager()` to trigger this ability in the boxing transpiler. ([#143](https://github.com/Qiskit/samplomatic/issues/143))
- Added a warning at import time about the beta status of this project. The warning should only be raised once per version, see the [contribution guidelines](CONTRIBUTING.md) for details. ([#132](https://github.com/Qiskit/samplomatic/issues/132))

### Changed

- Removed `NoiseInjectionStrategy.NONE` as it is now redundant with one of the supported values for `AddInjectNoise.targets`. ([#143](https://github.com/Qiskit/samplomatic/issues/143))

### Fixed

- Fixed a bug where `Samplex.__str__()` would raise an error for samplexes that require a noise model. ([#124](https://github.com/Qiskit/samplomatic/issues/124))


## [0.8.0](https://github.com/Qiskit/samplomatic/tree/0.8.0) - 2025-09-22

### Added

- Added ``add_twirling``, ``add_basis_transform``, and ``prefix_ref`` arguments to ``GroupMeasIntoBoxes`` to allow specifying what annotations should be placed on the boxes containing measurements.
  Added ``measure_annotations`` argument to the boxing passmanager to allow specifying what annotations should be placed on the boxes containing measurements. ([#96](https://github.com/Qiskit/samplomatic/issues/96))
- Added `InlineBoxes` pass to inline every box in the input circuit, replacing it with its content. ([#123](https://github.com/Qiskit/samplomatic/issues/123))

### Changed

- Changed the minimal supported Python version to 3.9. ([#119](https://github.com/Qiskit/samplomatic/issues/119))
- Changed `parameter_values` output type of `Samplex.sample` from `np.float64` to `np.float32`. ([#120](https://github.com/Qiskit/samplomatic/issues/120))

### Fixed

- Fixed a bug where ``GroupGatesIntoBoxes`` would group gates in a suboptimal way ([#110](https://github.com/Qiskit/samplomatic/issues/110))


## [0.7.0](https://github.com/Qiskit/samplomatic/tree/0.7.0) - 2025-09-15

### Removed

- Removed the `PauliRegister.from_paulis` method. ([#14](https://github.com/Qiskit/samplomatic/issues/14))

### Added

- Added a `width` argument to `TensorInterface.describe()` for text wrapping, and added this description to `Samplex.__str__()`. ([#104](https://github.com/Qiskit/samplomatic/issues/104))
- Added a `NoiseModelRequirement` class that describes a noise model required by a `Samplex` at sample time.
  Added a `Samplex.noise_models` property containing a dictionary of `NoiseModelRequirement`s. ([#112](https://github.com/Qiskit/samplomatic/issues/112))
- Added `InjectNoise` and `BasisTransform` to the top-level module, allowing, for example, `from samplomatic import InjectNoise, BasisTransform`. ([#117](https://github.com/Qiskit/samplomatic/issues/117))

### Changed

- Measurement flips are now returned with shape `(num_randomizations, 1, num_qubits)` to facilitate processing against a shots axis.
  Previously, they would be returned as `(num_randomizations, num_qubits)`. ([#105](https://github.com/Qiskit/samplomatic/issues/105))
- In order to facilitate broadcasting, `Samplex.sample()` now expects an array of rates and a `qiskit.quantum_info.QubitSparsePauliList` for each noise reference.
  Previously, it expected a `qiskit.quantum_info.PauliLindbladMap`.
  This change is reflected in `Samplex.inputs()` which now requires a `qiskit.quantum_info.QubitSparsePauliList` for each element of `Samplex.noise_models`.
  The returned `TensorInterface` object then contains the bound `QubitSparsePauliList`s, as well as `TensorSpecification`s for the rates, the scale, and the local scales. ([#112](https://github.com/Qiskit/samplomatic/issues/112))

### Fixed

- `Samplex.sample` arguments corresponding to `BasisTransform` and `InjectNoise` annotations are indexed in physical qubit order, in other words, the order of the qubits in the outer-most circuit, restricted to those used by the box.
  Previously, they followed the order of `CircuitInstruction.qubits`. ([#116](https://github.com/Qiskit/samplomatic/issues/116))

### Improved

- The `ParameterExpressionTable.evaluate` method now uses `ParameterExpression.bind_all` to increase performance. ([#13](https://github.com/Qiskit/samplomatic/issues/13))
- The `InjectNoise.sample` now uses the `QubitSparsePauliList.to_dense_array` method for increased performance. ([#14](https://github.com/Qiskit/samplomatic/issues/14))


## [0.6.0](https://github.com/Qiskit/samplomatic/tree/0.6.0) - 2025-09-03

### Added

- Added an `optional` field to `Specification`. ([#94](https://github.com/Qiskit/samplomatic/issues/94))

### Changed

- Modified `undress_box` so that if the input box contains no ``Twirl`` annotation, it returns a copy of the box rather than the box itself. ([#98](https://github.com/Qiskit/samplomatic/issues/98))

### Fixed

- Fixed a bug where the `modifier_ref`s of `InjectNoise` annotations were not being added to a samplex. ([#94](https://github.com/Qiskit/samplomatic/issues/94))
- Fixed a bug with imports for `numpy` versions older than `2.0.0`. ([#99](https://github.com/Qiskit/samplomatic/issues/99))


## [0.5.0](https://github.com/Qiskit/samplomatic/tree/0.5.0) - 2025-08-26

### Added

- Added new boolean option `remove_barriers` to `generate_boxing_pass_manager()` that adds the `RemoveBarriers` pass to the returned pass manager when true. ([#88](https://github.com/Qiskit/samplomatic/issues/88))

### Changed

- The pass manager returned by `generate_boxing_pass_manager()` now removes all pre-existing barriers, by default. ([#88](https://github.com/Qiskit/samplomatic/issues/88))


## [0.4.0](https://github.com/Qiskit/samplomatic/tree/0.4.0) - 2025-08-26

### Added

- Added support for measurements after twirled measurements. ([#82](https://github.com/Qiskit/samplomatic/issues/82))

### Changed

- Moved `num_randomizations` back to a kwarg of `Samplex.sample()`. This has flip-flopped a couple of times as we optimize workflow. ([#84](https://github.com/Qiskit/samplomatic/issues/84))

### Fixed

- Fixed a bug in `TensorInterface.__getitem__` for non-string inputs where it was incorrectly attempting to slice arrays whose shape did not match the full broadcasted shape of the interface. ([#83](https://github.com/Qiskit/samplomatic/issues/83))
- Fixed serialization of `Samplex` by including the passthrough parameters field.
  Previously, this would result in inconsistent output parameter values when sampling from the same samplex with the same input arguments. ([#86](https://github.com/Qiskit/samplomatic/issues/86))


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
