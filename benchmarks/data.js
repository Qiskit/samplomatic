window.BENCHMARK_DATA = {
  "lastUpdate": 1773248194424,
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
          "id": "8ddfb63ebd0427116f57beaf41f5f1c660a169ea",
          "message": "Improve benchmark plotters with zoom, and invert y-axis (#330)\n\n## Summary\n\n<!--\nFixes/Closes/Part of: #...\n-->\n\n## Details and comments\n\nClaude Opus 4.6",
          "timestamp": "2026-03-11T12:49:40-04:00",
          "tree_id": "712ac38564fa58fc06b2c5164de15422d650143a",
          "url": "https://github.com/Qiskit/samplomatic/commit/8ddfb63ebd0427116f57beaf41f5f1c660a169ea"
        },
        "date": 1773248191977,
        "tool": "pytest",
        "benches": [
          {
            "name": "test/performance/test_builder.py::TestBuilder::test_building_5k_circuit[96-5000]",
            "value": 0.1913764723458426,
            "unit": "iter/sec",
            "range": "stddev: 0.08495833604392669",
            "extra": "mean: 5.225302712200002 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.13945968028422917,
            "unit": "iter/sec",
            "range": "stddev: 0.06354204893931864",
            "extra": "mean: 7.170531281600001 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.08460720791187884,
            "unit": "iter/sec",
            "range": "stddev: 0.21283815459260794",
            "extra": "mean: 11.819323964 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.08186026502560635,
            "unit": "iter/sec",
            "range": "stddev: 0.18829214192608754",
            "extra": "mean: 12.215938950200007 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 1.6087048921271607,
            "unit": "iter/sec",
            "range": "stddev: 0.00352971775225028",
            "extra": "mean: 621.6180512000051 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 0.8794855562797648,
            "unit": "iter/sec",
            "range": "stddev: 0.10668301664930435",
            "extra": "mean: 1.1370283376000088 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialized_size[100-5000]",
            "value": 1.5955955934911086,
            "unit": "iter/sec",
            "range": "stddev: 0.00358574201188042",
            "extra": "mean: 626.7252204000101 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[no_modification-96-5000]",
            "value": 0.5081033140154628,
            "unit": "iter/sec",
            "range": "stddev: 0.03297803954467745",
            "extra": "mean: 1.9681036758000119 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[individual_modification-96-5000]",
            "value": 0.4660554993440714,
            "unit": "iter/sec",
            "range": "stddev: 0.04153764533141955",
            "extra": "mean: 2.14566720360001 sec\nrounds: 5"
          }
        ]
      }
    ]
  }
}