window.BENCHMARK_DATA = {
  "lastUpdate": 1773192285947,
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
          "id": "a468126d394c8c00f839611990fc6ef2f7750def",
          "message": "Update backfill to properly purge changes between installs (#326)\n\n## Summary\n\n<!--\nFixes/Closes/Part of: #...\n-->\n\n## Details and comments",
          "timestamp": "2026-03-10T19:45:48-04:00",
          "tree_id": "f0e6f1ac5a0d114684595d49b272b626265b7943",
          "url": "https://github.com/Qiskit/samplomatic/commit/a468126d394c8c00f839611990fc6ef2f7750def"
        },
        "date": 1773186755803,
        "tool": "pytest",
        "benches": [
          {
            "name": "test/performance/test_builder.py::TestBuilder::test_building_5k_circuit[96-5000]",
            "value": 0.20116807000653986,
            "unit": "iter/sec",
            "range": "stddev: 0.07914911698205604",
            "extra": "mean: 4.970967808 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.13491669191671002,
            "unit": "iter/sec",
            "range": "stddev: 0.06821220367150499",
            "extra": "mean: 7.411981318200003 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.08126449548490094,
            "unit": "iter/sec",
            "range": "stddev: 0.07281848766285302",
            "extra": "mean: 12.305496933600006 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.08081243535301852,
            "unit": "iter/sec",
            "range": "stddev: 0.0853505756092796",
            "extra": "mean: 12.374333178200004 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 1.6361996496519635,
            "unit": "iter/sec",
            "range": "stddev: 0.0030213624115173533",
            "extra": "mean: 611.1723591999976 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 0.9134175850093538,
            "unit": "iter/sec",
            "range": "stddev: 0.06940116987987192",
            "extra": "mean: 1.0947895205999998 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialized_size[100-5000]",
            "value": 1.630780777921418,
            "unit": "iter/sec",
            "range": "stddev: 0.003731613575464637",
            "extra": "mean: 613.2032052000227 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[no_modification-96-5000]",
            "value": 0.5257298406555231,
            "unit": "iter/sec",
            "range": "stddev: 0.02045106279316199",
            "extra": "mean: 1.9021176327999911 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[individual_modification-96-5000]",
            "value": 0.488254593158779,
            "unit": "iter/sec",
            "range": "stddev: 0.017159239728874776",
            "extra": "mean: 2.0481118129999913 sec\nrounds: 5"
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
          "id": "e90a97db8ec83cbd56c0d1be5cbea7ae81297d57",
          "message": "Fix the backfill benchmark github action again (#327)\n\n## Summary\n\n\n## Details and comments",
          "timestamp": "2026-03-10T21:17:41-04:00",
          "tree_id": "aaa32dddce51e80e5f3747071bda0ce426196fd4",
          "url": "https://github.com/Qiskit/samplomatic/commit/e90a97db8ec83cbd56c0d1be5cbea7ae81297d57"
        },
        "date": 1773192283193,
        "tool": "pytest",
        "benches": [
          {
            "name": "test/performance/test_builder.py::TestBuilder::test_building_5k_circuit[96-5000]",
            "value": 0.1856096025565623,
            "unit": "iter/sec",
            "range": "stddev: 0.09730887653233401",
            "extra": "mean: 5.387652288600004 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.1379568468862267,
            "unit": "iter/sec",
            "range": "stddev: 0.07097952966903694",
            "extra": "mean: 7.248643489400001 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.08462823664817108,
            "unit": "iter/sec",
            "range": "stddev: 0.05448136159211856",
            "extra": "mean: 11.816387054800003 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.08442716093061489,
            "unit": "iter/sec",
            "range": "stddev: 0.0798351122549935",
            "extra": "mean: 11.844529520799995 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 1.5882690549252427,
            "unit": "iter/sec",
            "range": "stddev: 0.004594096095119756",
            "extra": "mean: 629.6162460000005 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 0.8162676154143023,
            "unit": "iter/sec",
            "range": "stddev: 0.14195494140748535",
            "extra": "mean: 1.2250884159999942 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialized_size[100-5000]",
            "value": 1.5851565434025783,
            "unit": "iter/sec",
            "range": "stddev: 0.00866910563773102",
            "extra": "mean: 630.8525199999963 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[no_modification-96-5000]",
            "value": 0.47266778970661855,
            "unit": "iter/sec",
            "range": "stddev: 0.02020137259829391",
            "extra": "mean: 2.1156508265999947 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[individual_modification-96-5000]",
            "value": 0.43648562591237167,
            "unit": "iter/sec",
            "range": "stddev: 0.04539113394741829",
            "extra": "mean: 2.291026188799992 sec\nrounds: 5"
          }
        ]
      }
    ]
  }
}