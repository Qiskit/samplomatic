window.BENCHMARK_DATA = {
  "lastUpdate": 1773253836191,
  "repoUrl": "https://github.com/Qiskit/samplomatic",
  "entries": {
    "Benchmark": [
      {
        "commit": {
          "id": "e90a97db8ec83cbd56c0d1be5cbea7ae81297d57",
          "message": "Fix the backfill benchmark github action again (#327)",
          "timestamp": "2026-03-10T21:17:41-04:00",
          "url": "https://github.com/Qiskit/samplomatic/commit/e90a97db8ec83cbd56c0d1be5cbea7ae81297d57",
          "author": {
            "name": "Ian Hincks",
            "email": "ian.hincks@gmail.com",
            "username": ""
          },
          "committer": {
            "name": "Ian Hincks",
            "email": "ian.hincks@gmail.com",
            "username": ""
          }
        },
        "date": "2026-03-10T21:17:41-04:00",
        "tool": "pytest",
        "benches": [
          {
            "name": "test/performance/test_builder.py::TestBuilder::test_building_5k_circuit[96-5000]",
            "value": 0.18673278461367526,
            "unit": "iter/sec",
            "range": "stddev: 0.07969933066828488",
            "extra": "mean: 5.36 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.13960727069466786,
            "unit": "iter/sec",
            "range": "stddev: 0.02907357013203025",
            "extra": "mean: 7.16 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.08535192812715567,
            "unit": "iter/sec",
            "range": "stddev: 0.06483187696032491",
            "extra": "mean: 11.72 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.08345944552831859,
            "unit": "iter/sec",
            "range": "stddev: 0.06699273705453296",
            "extra": "mean: 11.98 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 1.563874268686216,
            "unit": "iter/sec",
            "range": "stddev: 0.0032610587081970755",
            "extra": "mean: 639.44 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 0.8436988805379493,
            "unit": "iter/sec",
            "range": "stddev: 0.13760438562093819",
            "extra": "mean: 1.19 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialized_size[100-5000]",
            "value": 1.5426379430497057,
            "unit": "iter/sec",
            "range": "stddev: 0.005674283979472406",
            "extra": "mean: 648.24 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[no_modification-96-5000]",
            "value": 0.4794248198526477,
            "unit": "iter/sec",
            "range": "stddev: 0.030573220845088157",
            "extra": "mean: 2.09 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[individual_modification-96-5000]",
            "value": 0.4443626197486392,
            "unit": "iter/sec",
            "range": "stddev: 0.09134210858021656",
            "extra": "mean: 2.25 sec\nrounds: 5"
          }
        ]
      },
      {
        "commit": {
          "id": "237db7266c3a1adf40bb2edd61a957fdf581d83a",
          "message": "Update Backfill Benchmarks GHA to backfill every commit in a range (#328)",
          "timestamp": "2026-03-10T22:56:59-04:00",
          "url": "https://github.com/Qiskit/samplomatic/commit/237db7266c3a1adf40bb2edd61a957fdf581d83a",
          "author": {
            "name": "Ian Hincks",
            "email": "ian.hincks@gmail.com",
            "username": ""
          },
          "committer": {
            "name": "Ian Hincks",
            "email": "ian.hincks@gmail.com",
            "username": ""
          }
        },
        "date": "2026-03-10T22:56:59-04:00",
        "tool": "pytest",
        "benches": [
          {
            "name": "test/performance/test_builder.py::TestBuilder::test_building_5k_circuit[96-5000]",
            "value": 0.1868649207960929,
            "unit": "iter/sec",
            "range": "stddev: 0.19507489459023142",
            "extra": "mean: 5.35 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.13879860208694758,
            "unit": "iter/sec",
            "range": "stddev: 0.07148864034959922",
            "extra": "mean: 7.20 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.08607146092500807,
            "unit": "iter/sec",
            "range": "stddev: 0.09359766962362659",
            "extra": "mean: 11.62 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.08488495029709514,
            "unit": "iter/sec",
            "range": "stddev: 0.07419385111196342",
            "extra": "mean: 11.78 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 1.579744510826967,
            "unit": "iter/sec",
            "range": "stddev: 0.006219195242670453",
            "extra": "mean: 633.01 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 0.8501176378590414,
            "unit": "iter/sec",
            "range": "stddev: 0.11642713910904771",
            "extra": "mean: 1.18 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialized_size[100-5000]",
            "value": 1.564291339428166,
            "unit": "iter/sec",
            "range": "stddev: 0.004522421758674853",
            "extra": "mean: 639.27 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[no_modification-96-5000]",
            "value": 0.4966101641973174,
            "unit": "iter/sec",
            "range": "stddev: 0.01695411362187943",
            "extra": "mean: 2.01 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[individual_modification-96-5000]",
            "value": 0.45896875233564133,
            "unit": "iter/sec",
            "range": "stddev: 0.020174521445634582",
            "extra": "mean: 2.18 sec\nrounds: 5"
          }
        ]
      },
      {
        "commit": {
          "id": "e038c32c0a86c5c486a4be7720061a7926798812",
          "message": "Fix benchmark assembler script and add links to benchmarks (#329)",
          "timestamp": "2026-03-11T09:12:09-04:00",
          "url": "https://github.com/Qiskit/samplomatic/commit/e038c32c0a86c5c486a4be7720061a7926798812",
          "author": {
            "name": "Ian Hincks",
            "email": "ian.hincks@gmail.com",
            "username": ""
          },
          "committer": {
            "name": "Ian Hincks",
            "email": "ian.hincks@gmail.com",
            "username": ""
          }
        },
        "date": "2026-03-11T09:12:09-04:00",
        "tool": "pytest",
        "benches": [
          {
            "name": "test/performance/test_builder.py::TestBuilder::test_building_5k_circuit[96-5000]",
            "value": 0.18799814764522815,
            "unit": "iter/sec",
            "range": "stddev: 0.116054006563791",
            "extra": "mean: 5.32 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.13926904124230446,
            "unit": "iter/sec",
            "range": "stddev: 0.0428569156649494",
            "extra": "mean: 7.18 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.08503611233284948,
            "unit": "iter/sec",
            "range": "stddev: 0.057789655850692234",
            "extra": "mean: 11.76 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.08417852576592705,
            "unit": "iter/sec",
            "range": "stddev: 0.13110475910447345",
            "extra": "mean: 11.88 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 1.5786942600264424,
            "unit": "iter/sec",
            "range": "stddev: 0.0033803598656567996",
            "extra": "mean: 633.43 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 0.8514306701769737,
            "unit": "iter/sec",
            "range": "stddev: 0.10529240202829865",
            "extra": "mean: 1.17 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialized_size[100-5000]",
            "value": 1.5852734041093615,
            "unit": "iter/sec",
            "range": "stddev: 0.003683044598816603",
            "extra": "mean: 630.81 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[no_modification-96-5000]",
            "value": 0.4932012078362577,
            "unit": "iter/sec",
            "range": "stddev: 0.0455353579418571",
            "extra": "mean: 2.03 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[individual_modification-96-5000]",
            "value": 0.4497078239363575,
            "unit": "iter/sec",
            "range": "stddev: 0.03122632449303833",
            "extra": "mean: 2.22 sec\nrounds: 5"
          }
        ]
      },
      {
        "commit": {
          "id": "8ddfb63ebd0427116f57beaf41f5f1c660a169ea",
          "message": "Improve benchmark plotters with zoom, and invert y-axis (#330)",
          "timestamp": "2026-03-11T12:49:40-04:00",
          "url": "https://github.com/Qiskit/samplomatic/commit/8ddfb63ebd0427116f57beaf41f5f1c660a169ea",
          "author": {
            "name": "Ian Hincks",
            "email": "ian.hincks@gmail.com",
            "username": ""
          },
          "committer": {
            "name": "Ian Hincks",
            "email": "ian.hincks@gmail.com",
            "username": ""
          }
        },
        "date": "2026-03-11T12:49:40-04:00",
        "tool": "pytest",
        "benches": [
          {
            "name": "test/performance/test_builder.py::TestBuilder::test_building_5k_circuit[96-5000]",
            "value": 0.18806666851220846,
            "unit": "iter/sec",
            "range": "stddev: 0.1568339785657652",
            "extra": "mean: 5.32 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.1388322592990197,
            "unit": "iter/sec",
            "range": "stddev: 0.05941249981880495",
            "extra": "mean: 7.20 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.08477668264891922,
            "unit": "iter/sec",
            "range": "stddev: 0.04587157789907063",
            "extra": "mean: 11.80 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.0843728421828071,
            "unit": "iter/sec",
            "range": "stddev: 0.06782965951776877",
            "extra": "mean: 11.85 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 1.5970790012791305,
            "unit": "iter/sec",
            "range": "stddev: 0.004281044975029587",
            "extra": "mean: 626.14 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 0.8517880256210631,
            "unit": "iter/sec",
            "range": "stddev: 0.12070824329875778",
            "extra": "mean: 1.17 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialized_size[100-5000]",
            "value": 1.5813570707873015,
            "unit": "iter/sec",
            "range": "stddev: 0.00512405108204501",
            "extra": "mean: 632.37 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[no_modification-96-5000]",
            "value": 0.4449333621390283,
            "unit": "iter/sec",
            "range": "stddev: 0.04573631835891481",
            "extra": "mean: 2.25 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[individual_modification-96-5000]",
            "value": 0.41368326100209357,
            "unit": "iter/sec",
            "range": "stddev: 0.056742814320970184",
            "extra": "mean: 2.42 sec\nrounds: 5"
          }
        ]
      },
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
          "id": "564e03195c72e7991755b5d880d0d0e1f5aefa28",
          "message": "Fix sorting during benchmark data merge (#331)\n\n## Summary\n\n<!--\nFixes/Closes/Part of: #...\n-->\n\n## Details and comments\n\nClaude Opus 4.6",
          "timestamp": "2026-03-11T14:18:00-04:00",
          "tree_id": "9ece725194cb9a06570c87eb38ad9bcdb3d0914f",
          "url": "https://github.com/Qiskit/samplomatic/commit/564e03195c72e7991755b5d880d0d0e1f5aefa28"
        },
        "date": 1773253517105,
        "tool": "pytest",
        "benches": [
          {
            "name": "test/performance/test_builder.py::TestBuilder::test_building_5k_circuit[96-5000]",
            "value": 0.17955385031977508,
            "unit": "iter/sec",
            "range": "stddev: 0.13798618769369966",
            "extra": "mean: 5.569359822799998 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.1324340374136321,
            "unit": "iter/sec",
            "range": "stddev: 0.08132839031344924",
            "extra": "mean: 7.5509288965999986 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.08119331986230956,
            "unit": "iter/sec",
            "range": "stddev: 0.08585039275450151",
            "extra": "mean: 12.316284168399994 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.08174859941275633,
            "unit": "iter/sec",
            "range": "stddev: 0.09912041009409263",
            "extra": "mean: 12.232625478400019 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 1.5602443527888417,
            "unit": "iter/sec",
            "range": "stddev: 0.00798815481677164",
            "extra": "mean: 640.9252488000106 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 0.8150030230524054,
            "unit": "iter/sec",
            "range": "stddev: 0.13487599197000533",
            "extra": "mean: 1.2269893138000043 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialized_size[100-5000]",
            "value": 1.5453691951634296,
            "unit": "iter/sec",
            "range": "stddev: 0.0035648173559495845",
            "extra": "mean: 647.0945604000121 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[no_modification-96-5000]",
            "value": 0.4773406866741959,
            "unit": "iter/sec",
            "range": "stddev: 0.02404299883574499",
            "extra": "mean: 2.094939794400011 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[individual_modification-96-5000]",
            "value": 0.42861610587331567,
            "unit": "iter/sec",
            "range": "stddev: 0.0337814691242858",
            "extra": "mean: 2.3330901156000095 sec\nrounds: 5"
          }
        ]
      },
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
          "id": "b2c40508ed0abd3e3b75836e2b5a411efad4c273",
          "message": "Fix AddInjectNoise/BoxKey parallelization bugs (#323)\n\n## Summary\n\nMade `BoxKey` hashing deterministic across Python processes by using\nSHA-256 instead of the built-in `hash()`, which is randomized by\n`PYTHONHASHSEED`. This caused `AddInjectNoise` to generate different\n`ref` names for identical boxes across runs, since it derived short hash\nkeys from `BoxKey.__hash__`. Also fixed a bug in\n`AddInjectNoise._get_ref()` where the computed ref was not being cached\ncorrectly. It is expected that these bugs were only visible when this\npass was being run in parallel by the qiskit pass manager.\n\n\n## Details and comments\n\nI found this because the `test_consistent_naming()` test of\nAddInjectNoise was randomly failing for me locally.",
          "timestamp": "2026-03-11T15:53:30-02:30",
          "tree_id": "f61e8f356ad795a0fb4e355600b22cb82c0bd08a",
          "url": "https://github.com/Qiskit/samplomatic/commit/b2c40508ed0abd3e3b75836e2b5a411efad4c273"
        },
        "date": 1773253833813,
        "tool": "pytest",
        "benches": [
          {
            "name": "test/performance/test_builder.py::TestBuilder::test_building_5k_circuit[96-5000]",
            "value": 0.1859978379488563,
            "unit": "iter/sec",
            "range": "stddev: 0.034497639740394145",
            "extra": "mean: 5.376406580999986 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.13765045510099722,
            "unit": "iter/sec",
            "range": "stddev: 0.02212918592781107",
            "extra": "mean: 7.264778015200005 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.08067189529673607,
            "unit": "iter/sec",
            "range": "stddev: 0.1150405609963219",
            "extra": "mean: 12.39589074139999 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.08348075760335251,
            "unit": "iter/sec",
            "range": "stddev: 0.0519090756008442",
            "extra": "mean: 11.97880839500001 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 1.5740045671108784,
            "unit": "iter/sec",
            "range": "stddev: 0.002236064289502702",
            "extra": "mean: 635.3221717999986 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 0.8380191793085057,
            "unit": "iter/sec",
            "range": "stddev: 0.09848346567724822",
            "extra": "mean: 1.1932901116000152 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialized_size[100-5000]",
            "value": 1.5855363060429988,
            "unit": "iter/sec",
            "range": "stddev: 0.0013537179710673985",
            "extra": "mean: 630.7014202000119 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[no_modification-96-5000]",
            "value": 0.46796274951298616,
            "unit": "iter/sec",
            "range": "stddev: 0.031667342255086404",
            "extra": "mean: 2.1369222251999984 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[individual_modification-96-5000]",
            "value": 0.43735574386617554,
            "unit": "iter/sec",
            "range": "stddev: 0.031859403305954104",
            "extra": "mean: 2.2864681990000006 sec\nrounds: 5"
          }
        ]
      }
    ]
  }
}