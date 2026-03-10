window.BENCHMARK_DATA = {
  "lastUpdate": 1773182075854,
  "repoUrl": "https://github.com/Qiskit/samplomatic",
  "entries": {
    "Benchmark": [
      {
        "commit": {
          "author": {
            "email": "ian.hincks@gmail.com",
            "name": "Ian Hincks",
            "username": "ihincks"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "db4a264164464eb6badc8ebd8c950f1e03ba9b5f",
          "message": "Update the Benchmarks GitHub Action to include github credentials (#325)\n\n## Summary\n\n<!--\nFixes/Closes/Part of: #...\n-->\n\n## Details and comments",
          "timestamp": "2026-03-10T18:27:41-04:00",
          "tree_id": "5da7fb280257bd7904a1116e125c360e0bd88ad5",
          "url": "https://github.com/Qiskit/samplomatic/commit/db4a264164464eb6badc8ebd8c950f1e03ba9b5f"
        },
        "date": 1773182073435,
        "tool": "pytest",
        "benches": [
          {
            "name": "test/performance/test_builder.py::TestBuilder::test_building_5k_circuit[96-5000]",
            "value": 0.1828089747522916,
            "unit": "iter/sec",
            "range": "stddev: 0.11790189882100935",
            "extra": "mean: 5.470190954 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.13890179811719358,
            "unit": "iter/sec",
            "range": "stddev: 0.04615486910619021",
            "extra": "mean: 7.1993308478000015 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.08472760490256868,
            "unit": "iter/sec",
            "range": "stddev: 0.0836239674376115",
            "extra": "mean: 11.802528835200002 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.0842486638675701,
            "unit": "iter/sec",
            "range": "stddev: 0.014447595358902063",
            "extra": "mean: 11.869624443800001 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 1.57530743057093,
            "unit": "iter/sec",
            "range": "stddev: 0.0038057014552584554",
            "extra": "mean: 634.7967263999863 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 0.8537486664780951,
            "unit": "iter/sec",
            "range": "stddev: 0.12389424670496572",
            "extra": "mean: 1.1713049041999966 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialized_size[100-5000]",
            "value": 1.5704332901267708,
            "unit": "iter/sec",
            "range": "stddev: 0.0060239314683213875",
            "extra": "mean: 636.766939600011 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[no_modification-96-5000]",
            "value": 0.4838396464136446,
            "unit": "iter/sec",
            "range": "stddev: 0.020036911667702276",
            "extra": "mean: 2.066800452199982 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[individual_modification-96-5000]",
            "value": 0.44729545842226853,
            "unit": "iter/sec",
            "range": "stddev: 0.08978960204355697",
            "extra": "mean: 2.235658737799997 sec\nrounds: 5"
          }
        ]
      }
    ]
  }
}