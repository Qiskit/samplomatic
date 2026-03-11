window.BENCHMARK_DATA = {
  "lastUpdate": 1773235159275,
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
          "id": "e038c32c0a86c5c486a4be7720061a7926798812",
          "message": "Fix benchmark assembler script and add links to benchmarks (#329)\n\n## Summary\n\n<!--\nFixes/Closes/Part of: #...\n-->\n\n## Details and comments",
          "timestamp": "2026-03-11T09:12:09-04:00",
          "tree_id": "8d1a611231e68a409cd9e3cd187b4499f7e6670d",
          "url": "https://github.com/Qiskit/samplomatic/commit/e038c32c0a86c5c486a4be7720061a7926798812"
        },
        "date": 1773235156507,
        "tool": "pytest",
        "benches": [
          {
            "name": "test/performance/test_builder.py::TestBuilder::test_building_5k_circuit[96-5000]",
            "value": 0.18910974558345958,
            "unit": "iter/sec",
            "range": "stddev: 0.08021077596451134",
            "extra": "mean: 5.287934775199997 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.13502698978195,
            "unit": "iter/sec",
            "range": "stddev: 0.05398181548313707",
            "extra": "mean: 7.4059267826 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.08288785894405151,
            "unit": "iter/sec",
            "range": "stddev: 0.07637577658086332",
            "extra": "mean: 12.064493072199998 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.08093181045076066,
            "unit": "iter/sec",
            "range": "stddev: 0.09457642304779092",
            "extra": "mean: 12.356080933199996 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 1.605112177503586,
            "unit": "iter/sec",
            "range": "stddev: 0.004663127163673081",
            "extra": "mean: 623.0094158000156 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 0.8528879476233873,
            "unit": "iter/sec",
            "range": "stddev: 0.11896571738897659",
            "extra": "mean: 1.1724869636000221 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialized_size[100-5000]",
            "value": 1.604458159250128,
            "unit": "iter/sec",
            "range": "stddev: 0.005174728805304534",
            "extra": "mean: 623.2633703999909 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[no_modification-96-5000]",
            "value": 0.44126105107822194,
            "unit": "iter/sec",
            "range": "stddev: 0.03801204700898686",
            "extra": "mean: 2.2662321942000063 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[individual_modification-96-5000]",
            "value": 0.41661361300611627,
            "unit": "iter/sec",
            "range": "stddev: 0.060270411436026815",
            "extra": "mean: 2.4003056280000123 sec\nrounds: 5"
          }
        ]
      }
    ]
  }
}