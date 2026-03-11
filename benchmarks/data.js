window.BENCHMARK_DATA = {
  "lastUpdate": 1773198215895,
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
          "id": "237db7266c3a1adf40bb2edd61a957fdf581d83a",
          "message": "Update Backfill Benchmarks GHA to backfill every commit in a range (#328)\n\n## Summary\n\n<!--\nFixes/Closes/Part of: #...\n-->\n\n## Details and comments",
          "timestamp": "2026-03-10T22:56:59-04:00",
          "tree_id": "38eadf86f1b005fbb4f379538fd1cbb281370fa3",
          "url": "https://github.com/Qiskit/samplomatic/commit/237db7266c3a1adf40bb2edd61a957fdf581d83a"
        },
        "date": 1773198213036,
        "tool": "pytest",
        "benches": [
          {
            "name": "test/performance/test_builder.py::TestBuilder::test_building_5k_circuit[96-5000]",
            "value": 0.20429808812014813,
            "unit": "iter/sec",
            "range": "stddev: 0.046100876183556495",
            "extra": "mean: 4.894808410599995 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.13986409471987865,
            "unit": "iter/sec",
            "range": "stddev: 0.060997621960186904",
            "extra": "mean: 7.149797823400002 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.08599898531881835,
            "unit": "iter/sec",
            "range": "stddev: 0.0440911556566209",
            "extra": "mean: 11.628044171600004 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.08550194115630723,
            "unit": "iter/sec",
            "range": "stddev: 0.0659876313071138",
            "extra": "mean: 11.695640899800003 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 1.6243719557102683,
            "unit": "iter/sec",
            "range": "stddev: 0.001281430773694617",
            "extra": "mean: 615.6225466000137 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 0.8889622195009046,
            "unit": "iter/sec",
            "range": "stddev: 0.08058694617175893",
            "extra": "mean: 1.124907198599999 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialized_size[100-5000]",
            "value": 1.620323305079359,
            "unit": "iter/sec",
            "range": "stddev: 0.002976528441021647",
            "extra": "mean: 617.1607832000063 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[no_modification-96-5000]",
            "value": 0.5430563597933624,
            "unit": "iter/sec",
            "range": "stddev: 0.009249784041521809",
            "extra": "mean: 1.8414294980000023 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[individual_modification-96-5000]",
            "value": 0.5001159478815856,
            "unit": "iter/sec",
            "range": "stddev: 0.01775310537266612",
            "extra": "mean: 1.9995363160000124 sec\nrounds: 5"
          }
        ]
      }
    ]
  }
}