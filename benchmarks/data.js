window.BENCHMARK_DATA = {
  "lastUpdate": 0,
  "repoUrl": "https://github.com/Qiskit/samplomatic",
  "entries": {
    "Benchmark": [
      {
        "commit": {
          "id": "bacc2ee9777d2748b0d1e6dcb6697b6ada38c7aa",
          "message": "Adding release.yml file so we can release on PyPi  (#63)",
          "timestamp": "2025-08-15T23:10:15+02:00",
          "url": "https://github.com/Qiskit/samplomatic/commit/bacc2ee9777d2748b0d1e6dcb6697b6ada38c7aa",
          "author": {
            "name": "Juan Gomez",
            "email": "atilag@gmail.com",
            "username": ""
          },
          "committer": {
            "name": "Juan Gomez",
            "email": "atilag@gmail.com",
            "username": ""
          }
        },
        "date": "2025-08-15T23:10:15+02:00",
        "tool": "pytest",
        "benches": [
          {
            "name": "test/performance/test_builder.py::TestBuilder::test_building_5k_circuit[5000-96]",
            "value": 0.14313880436621457,
            "unit": "iter/sec",
            "range": "stddev: 0.16722779040070004",
            "extra": "mean: 6.99 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[1650-5000-100]",
            "value": 0.1358138403779566,
            "unit": "iter/sec",
            "range": "stddev: 0.058629652608656026",
            "extra": "mean: 7.36 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-1650-5000-100]",
            "value": 0.11100859547491868,
            "unit": "iter/sec",
            "range": "stddev: 0.01808947966104024",
            "extra": "mean: 9.01 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-1650-5000-100]",
            "value": 0.11055837176016624,
            "unit": "iter/sec",
            "range": "stddev: 0.06514091840701275",
            "extra": "mean: 9.04 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[5000-100]",
            "value": 8.915136715537797,
            "unit": "iter/sec",
            "range": "stddev: 0.03681733786892988",
            "extra": "mean: 112.17 msec\nrounds: 11"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[5000-100]",
            "value": 4.7341107675309075,
            "unit": "iter/sec",
            "range": "stddev: 0.03487792279390053",
            "extra": "mean: 211.23 msec\nrounds: 6"
          }
        ]
      },
      {
        "commit": {
          "id": "40880bb557029407dd1ef6d4ccfe7d420daf831c",
          "message": "Add changelog for release 0.6.0 (#100)",
          "timestamp": "2025-09-03T14:50:35-04:00",
          "url": "https://github.com/Qiskit/samplomatic/commit/40880bb557029407dd1ef6d4ccfe7d420daf831c",
          "author": {
            "name": "joshuasn",
            "email": "53916441+joshuasn@users.noreply.github.com",
            "username": ""
          },
          "committer": {
            "name": "joshuasn",
            "email": "53916441+joshuasn@users.noreply.github.com",
            "username": ""
          }
        },
        "date": "2025-09-03T14:50:35-04:00",
        "tool": "pytest",
        "benches": [
          {
            "name": "test/performance/test_builder.py::TestBuilder::test_building_5k_circuit[96-5000]",
            "value": 0.14418361274495606,
            "unit": "iter/sec",
            "range": "stddev: 0.04555010891939101",
            "extra": "mean: 6.94 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.13510267127043868,
            "unit": "iter/sec",
            "range": "stddev: 0.05094598546210305",
            "extra": "mean: 7.40 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.10950495262079003,
            "unit": "iter/sec",
            "range": "stddev: 0.05839524092349505",
            "extra": "mean: 9.13 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.10031665145646532,
            "unit": "iter/sec",
            "range": "stddev: 0.02108544735950017",
            "extra": "mean: 9.97 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 8.889002280234301,
            "unit": "iter/sec",
            "range": "stddev: 0.03625908073584268",
            "extra": "mean: 112.50 msec\nrounds: 11"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 5.16846159705988,
            "unit": "iter/sec",
            "range": "stddev: 0.0022601296455139275",
            "extra": "mean: 193.48 msec\nrounds: 5"
          }
        ]
      },
      {
        "commit": {
          "id": "f861579f8967c095beebac2326b5c996f3cd3c26",
          "message": "Add changelog for release 0.7.0 (#121)",
          "timestamp": "2025-09-15T09:43:23-04:00",
          "url": "https://github.com/Qiskit/samplomatic/commit/f861579f8967c095beebac2326b5c996f3cd3c26",
          "author": {
            "name": "joshuasn",
            "email": "53916441+joshuasn@users.noreply.github.com",
            "username": ""
          },
          "committer": {
            "name": "joshuasn",
            "email": "53916441+joshuasn@users.noreply.github.com",
            "username": ""
          }
        },
        "date": "2025-09-15T09:43:23-04:00",
        "tool": "pytest",
        "benches": [
          {
            "name": "test/performance/test_builder.py::TestBuilder::test_building_5k_circuit[96-5000]",
            "value": 0.14294054352659863,
            "unit": "iter/sec",
            "range": "stddev: 0.10726854999830569",
            "extra": "mean: 7.00 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.1366212220765992,
            "unit": "iter/sec",
            "range": "stddev: 0.03177542396367562",
            "extra": "mean: 7.32 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.13189519953780332,
            "unit": "iter/sec",
            "range": "stddev: 0.048121235611882675",
            "extra": "mean: 7.58 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.13038070166299695,
            "unit": "iter/sec",
            "range": "stddev: 0.06098428477411048",
            "extra": "mean: 7.67 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 7.9123907127193736,
            "unit": "iter/sec",
            "range": "stddev: 0.03900501764080201",
            "extra": "mean: 126.38 msec\nrounds: 11"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 5.0623526943951545,
            "unit": "iter/sec",
            "range": "stddev: 0.0014338738221893249",
            "extra": "mean: 197.54 msec\nrounds: 6"
          }
        ]
      },
      {
        "commit": {
          "id": "6c4a5f833a5f25db231c2ae1165ef649d40cdf93",
          "message": "Add changelog for release 0.8.0 (#129)",
          "timestamp": "2025-09-22T12:22:02-04:00",
          "url": "https://github.com/Qiskit/samplomatic/commit/6c4a5f833a5f25db231c2ae1165ef649d40cdf93",
          "author": {
            "name": "joshuasn",
            "email": "53916441+joshuasn@users.noreply.github.com",
            "username": ""
          },
          "committer": {
            "name": "joshuasn",
            "email": "53916441+joshuasn@users.noreply.github.com",
            "username": ""
          }
        },
        "date": "2025-09-22T12:22:02-04:00",
        "tool": "pytest",
        "benches": [
          {
            "name": "test/performance/test_builder.py::TestBuilder::test_building_5k_circuit[96-5000]",
            "value": 0.14559675266398175,
            "unit": "iter/sec",
            "range": "stddev: 0.0423384883679152",
            "extra": "mean: 6.87 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.13803804900384212,
            "unit": "iter/sec",
            "range": "stddev: 0.029520258516438334",
            "extra": "mean: 7.24 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.1320665346336153,
            "unit": "iter/sec",
            "range": "stddev: 0.017639575239860567",
            "extra": "mean: 7.57 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.1305506865469412,
            "unit": "iter/sec",
            "range": "stddev: 0.0327293673505501",
            "extra": "mean: 7.66 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 7.861124365024852,
            "unit": "iter/sec",
            "range": "stddev: 0.03910775406479319",
            "extra": "mean: 127.21 msec\nrounds: 11"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 5.103538414090058,
            "unit": "iter/sec",
            "range": "stddev: 0.0009004393516572416",
            "extra": "mean: 195.94 msec\nrounds: 6"
          }
        ]
      },
      {
        "commit": {
          "id": "f7d461e8fc25a9877aec3a2766e6b46407b8b92f",
          "message": "Add changelog for release 0.9.0 (#144)",
          "timestamp": "2025-09-30T10:55:15-04:00",
          "url": "https://github.com/Qiskit/samplomatic/commit/f7d461e8fc25a9877aec3a2766e6b46407b8b92f",
          "author": {
            "name": "Samuele Ferracin",
            "email": "sam.ferracin@ibm.com",
            "username": ""
          },
          "committer": {
            "name": "Samuele Ferracin",
            "email": "sam.ferracin@ibm.com",
            "username": ""
          }
        },
        "date": "2025-09-30T10:55:15-04:00",
        "tool": "pytest",
        "benches": [
          {
            "name": "test/performance/test_builder.py::TestBuilder::test_building_5k_circuit[96-5000]",
            "value": 0.14703081086904454,
            "unit": "iter/sec",
            "range": "stddev: 0.055344869001631304",
            "extra": "mean: 6.80 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.13717659336404997,
            "unit": "iter/sec",
            "range": "stddev: 0.054326496142002446",
            "extra": "mean: 7.29 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.13126894911600184,
            "unit": "iter/sec",
            "range": "stddev: 0.025185949930861675",
            "extra": "mean: 7.62 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.1308823218396491,
            "unit": "iter/sec",
            "range": "stddev: 0.05985737746182248",
            "extra": "mean: 7.64 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 7.664505513248134,
            "unit": "iter/sec",
            "range": "stddev: 0.04281839792970566",
            "extra": "mean: 130.47 msec\nrounds: 11"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 5.07188550186927,
            "unit": "iter/sec",
            "range": "stddev: 0.0027984460295884667",
            "extra": "mean: 197.17 msec\nrounds: 5"
          }
        ]
      },
      {
        "commit": {
          "id": "f4c396b3bcbfeb88de2a8383e1412c5dec4db5a7",
          "message": "Fix doc deploy config, hopefully the last time (#177)",
          "timestamp": "2025-10-20T14:29:04-04:00",
          "url": "https://github.com/Qiskit/samplomatic/commit/f4c396b3bcbfeb88de2a8383e1412c5dec4db5a7",
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
        "date": "2025-10-20T14:29:04-04:00",
        "tool": "pytest",
        "benches": [
          {
            "name": "test/performance/test_builder.py::TestBuilder::test_building_5k_circuit[96-5000]",
            "value": 0.14437830428477108,
            "unit": "iter/sec",
            "range": "stddev: 0.13485170829119644",
            "extra": "mean: 6.93 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.13708057982682217,
            "unit": "iter/sec",
            "range": "stddev: 0.03997731767989056",
            "extra": "mean: 7.29 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.13139551859860252,
            "unit": "iter/sec",
            "range": "stddev: 0.028275205265003184",
            "extra": "mean: 7.61 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.1304853337468958,
            "unit": "iter/sec",
            "range": "stddev: 0.08205419306102991",
            "extra": "mean: 7.66 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 8.273478378276776,
            "unit": "iter/sec",
            "range": "stddev: 0.04015283999782146",
            "extra": "mean: 120.87 msec\nrounds: 10"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 4.953163230262663,
            "unit": "iter/sec",
            "range": "stddev: 0.0024332325137083866",
            "extra": "mean: 201.89 msec\nrounds: 5"
          }
        ]
      },
      {
        "commit": {
          "id": "607b61eef208356908845ebb13ad249ba96ac7c8",
          "message": "Update list of old documentation versions (#181)",
          "timestamp": "2025-10-22T15:36:48-04:00",
          "url": "https://github.com/Qiskit/samplomatic/commit/607b61eef208356908845ebb13ad249ba96ac7c8",
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
        "date": "2025-10-22T15:36:48-04:00",
        "tool": "pytest",
        "benches": [
          {
            "name": "test/performance/test_builder.py::TestBuilder::test_building_5k_circuit[96-5000]",
            "value": 0.14019782950927376,
            "unit": "iter/sec",
            "range": "stddev: 0.05131616439375866",
            "extra": "mean: 7.13 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.13455373495226014,
            "unit": "iter/sec",
            "range": "stddev: 0.06256480654080711",
            "extra": "mean: 7.43 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.12898764523913955,
            "unit": "iter/sec",
            "range": "stddev: 0.04090507838699",
            "extra": "mean: 7.75 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.12910284911692485,
            "unit": "iter/sec",
            "range": "stddev: 0.07969530946492044",
            "extra": "mean: 7.75 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 7.533030080762902,
            "unit": "iter/sec",
            "range": "stddev: 0.04802806627210476",
            "extra": "mean: 132.75 msec\nrounds: 10"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 4.611834447932001,
            "unit": "iter/sec",
            "range": "stddev: 0.002048180572710882",
            "extra": "mean: 216.83 msec\nrounds: 5"
          }
        ]
      },
      {
        "commit": {
          "id": "f10fc74f6abc5b5b72bfd0558b033f458d610b71",
          "message": "Add changelog for release 0.11.0 (#194)",
          "timestamp": "2025-10-28T11:06:38-04:00",
          "url": "https://github.com/Qiskit/samplomatic/commit/f10fc74f6abc5b5b72bfd0558b033f458d610b71",
          "author": {
            "name": "Samuele Ferracin",
            "email": "sam.ferracin@ibm.com",
            "username": ""
          },
          "committer": {
            "name": "Samuele Ferracin",
            "email": "sam.ferracin@ibm.com",
            "username": ""
          }
        },
        "date": "2025-10-28T11:06:38-04:00",
        "tool": "pytest",
        "benches": [
          {
            "name": "test/performance/test_builder.py::TestBuilder::test_building_5k_circuit[96-5000]",
            "value": 0.13379970090745108,
            "unit": "iter/sec",
            "range": "stddev: 0.09620309936612606",
            "extra": "mean: 7.47 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.1357612901469814,
            "unit": "iter/sec",
            "range": "stddev: 0.06335564652309172",
            "extra": "mean: 7.37 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.13123155289035154,
            "unit": "iter/sec",
            "range": "stddev: 0.11659146990682441",
            "extra": "mean: 7.62 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.13123316515941127,
            "unit": "iter/sec",
            "range": "stddev: 0.038388736115385805",
            "extra": "mean: 7.62 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 1.6171602384179833,
            "unit": "iter/sec",
            "range": "stddev: 0.003667944042291108",
            "extra": "mean: 618.37 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 0.8782138977923716,
            "unit": "iter/sec",
            "range": "stddev: 0.1269536932085573",
            "extra": "mean: 1.14 sec\nrounds: 5"
          }
        ]
      },
      {
        "commit": {
          "id": "c6baa4430b210da4e88bf88ed5195e4485214d65",
          "message": "Add changelog for release 0.12.0 (#222)",
          "timestamp": "2025-11-03T14:43:01-05:00",
          "url": "https://github.com/Qiskit/samplomatic/commit/c6baa4430b210da4e88bf88ed5195e4485214d65",
          "author": {
            "name": "joshuasn",
            "email": "53916441+joshuasn@users.noreply.github.com",
            "username": ""
          },
          "committer": {
            "name": "joshuasn",
            "email": "53916441+joshuasn@users.noreply.github.com",
            "username": ""
          }
        },
        "date": "2025-11-03T14:43:01-05:00",
        "tool": "pytest",
        "benches": [
          {
            "name": "test/performance/test_builder.py::TestBuilder::test_building_5k_circuit[96-5000]",
            "value": 0.1452265722584025,
            "unit": "iter/sec",
            "range": "stddev: 0.08834572082214547",
            "extra": "mean: 6.89 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.13765257111588342,
            "unit": "iter/sec",
            "range": "stddev: 0.05450738661738323",
            "extra": "mean: 7.26 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.13186522393100517,
            "unit": "iter/sec",
            "range": "stddev: 0.04347270516932866",
            "extra": "mean: 7.58 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.13122645986062775,
            "unit": "iter/sec",
            "range": "stddev: 0.07128176567246679",
            "extra": "mean: 7.62 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 1.6091346257650347,
            "unit": "iter/sec",
            "range": "stddev: 0.002774719053741736",
            "extra": "mean: 621.45 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 0.8897181060056429,
            "unit": "iter/sec",
            "range": "stddev: 0.0952547990703638",
            "extra": "mean: 1.12 sec\nrounds: 5"
          }
        ]
      },
      {
        "commit": {
          "id": "cee7b5db6d4e87b39fa83d98a809ca0481b5755e",
          "message": "Add changelog for release 0.13.0 (#230)",
          "timestamp": "2025-11-06T20:17:11-05:00",
          "url": "https://github.com/Qiskit/samplomatic/commit/cee7b5db6d4e87b39fa83d98a809ca0481b5755e",
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
        "date": "2025-11-06T20:17:11-05:00",
        "tool": "pytest",
        "benches": [
          {
            "name": "test/performance/test_builder.py::TestBuilder::test_building_5k_circuit[96-5000]",
            "value": 0.1448643408469775,
            "unit": "iter/sec",
            "range": "stddev: 0.09168344098060384",
            "extra": "mean: 6.90 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.13745116856145292,
            "unit": "iter/sec",
            "range": "stddev: 0.05566056733636042",
            "extra": "mean: 7.28 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.13154964072561323,
            "unit": "iter/sec",
            "range": "stddev: 0.08164653773710573",
            "extra": "mean: 7.60 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.13122951954988266,
            "unit": "iter/sec",
            "range": "stddev: 0.04289957082116645",
            "extra": "mean: 7.62 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 1.5864751692189154,
            "unit": "iter/sec",
            "range": "stddev: 0.0028204830131121185",
            "extra": "mean: 630.33 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 0.8842616401608892,
            "unit": "iter/sec",
            "range": "stddev: 0.10331709420762644",
            "extra": "mean: 1.13 sec\nrounds: 5"
          }
        ]
      },
      {
        "commit": {
          "id": "7d7d01dd53edb0d6cf280c802ba8d763191654da",
          "message": "Release 0.14.0 (#268)",
          "timestamp": "2025-12-09T09:34:44-05:00",
          "url": "https://github.com/Qiskit/samplomatic/commit/7d7d01dd53edb0d6cf280c802ba8d763191654da",
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
        "date": "2025-12-09T09:34:44-05:00",
        "tool": "pytest",
        "benches": [
          {
            "name": "test/performance/test_builder.py::TestBuilder::test_building_5k_circuit[96-5000]",
            "value": 0.1855456121961316,
            "unit": "iter/sec",
            "range": "stddev: 0.056915882835205205",
            "extra": "mean: 5.39 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.14038246312896951,
            "unit": "iter/sec",
            "range": "stddev: 0.036774011513108495",
            "extra": "mean: 7.12 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.13444666882015413,
            "unit": "iter/sec",
            "range": "stddev: 0.05225301074215418",
            "extra": "mean: 7.44 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.13427023699976706,
            "unit": "iter/sec",
            "range": "stddev: 0.04887173273622733",
            "extra": "mean: 7.45 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 1.6149804057898498,
            "unit": "iter/sec",
            "range": "stddev: 0.004004204399474817",
            "extra": "mean: 619.20 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 0.8984713463140115,
            "unit": "iter/sec",
            "range": "stddev: 0.08524664444576519",
            "extra": "mean: 1.11 sec\nrounds: 5"
          }
        ]
      },
      {
        "commit": {
          "id": "ec02cea34b720266b937372801b9b70f22fc6ec5",
          "message": "Release 0.15.0 (#278)",
          "timestamp": "2025-12-15T11:22:54-05:00",
          "url": "https://github.com/Qiskit/samplomatic/commit/ec02cea34b720266b937372801b9b70f22fc6ec5",
          "author": {
            "name": "joshuasn",
            "email": "53916441+joshuasn@users.noreply.github.com",
            "username": ""
          },
          "committer": {
            "name": "joshuasn",
            "email": "53916441+joshuasn@users.noreply.github.com",
            "username": ""
          }
        },
        "date": "2025-12-15T11:22:54-05:00",
        "tool": "pytest",
        "benches": [
          {
            "name": "test/performance/test_builder.py::TestBuilder::test_building_5k_circuit[96-5000]",
            "value": 0.20036158329266493,
            "unit": "iter/sec",
            "range": "stddev: 0.14764293863920616",
            "extra": "mean: 4.99 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.13716039854139525,
            "unit": "iter/sec",
            "range": "stddev: 0.07168338568398637",
            "extra": "mean: 7.29 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.08358394622484064,
            "unit": "iter/sec",
            "range": "stddev: 0.04503775173833114",
            "extra": "mean: 11.96 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.08350006871988976,
            "unit": "iter/sec",
            "range": "stddev: 0.06191968852322017",
            "extra": "mean: 11.98 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 1.6006064152221657,
            "unit": "iter/sec",
            "range": "stddev: 0.0036500422812792014",
            "extra": "mean: 624.76 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 0.8708358125796237,
            "unit": "iter/sec",
            "range": "stddev: 0.08884932439065023",
            "extra": "mean: 1.15 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[no_modification-96-5000]",
            "value": 0.5783318191412695,
            "unit": "iter/sec",
            "range": "stddev: 0.020157383598103998",
            "extra": "mean: 1.73 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[individual_modification-96-5000]",
            "value": 0.548051281660879,
            "unit": "iter/sec",
            "range": "stddev: 0.030619955391122944",
            "extra": "mean: 1.82 sec\nrounds: 5"
          }
        ]
      },
      {
        "commit": {
          "id": "67a9f57167528d5aec9d876b96e9d5964bce092b",
          "message": "Add changelog for release 0.16.0 (#295)",
          "timestamp": "2026-01-19T09:20:17-05:00",
          "url": "https://github.com/Qiskit/samplomatic/commit/67a9f57167528d5aec9d876b96e9d5964bce092b",
          "author": {
            "name": "joshuasn",
            "email": "53916441+joshuasn@users.noreply.github.com",
            "username": ""
          },
          "committer": {
            "name": "joshuasn",
            "email": "53916441+joshuasn@users.noreply.github.com",
            "username": ""
          }
        },
        "date": "2026-01-19T09:20:17-05:00",
        "tool": "pytest",
        "benches": [
          {
            "name": "test/performance/test_builder.py::TestBuilder::test_building_5k_circuit[96-5000]",
            "value": 0.20702849927072026,
            "unit": "iter/sec",
            "range": "stddev: 0.1253865931765818",
            "extra": "mean: 4.83 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.1377042327509705,
            "unit": "iter/sec",
            "range": "stddev: 0.031225354814206234",
            "extra": "mean: 7.26 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.08311168092423421,
            "unit": "iter/sec",
            "range": "stddev: 0.061773760938767804",
            "extra": "mean: 12.03 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.08308315762725477,
            "unit": "iter/sec",
            "range": "stddev: 0.05595430313274252",
            "extra": "mean: 12.04 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 1.6283383776557503,
            "unit": "iter/sec",
            "range": "stddev: 0.003537008505339746",
            "extra": "mean: 614.12 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 0.9060992514069184,
            "unit": "iter/sec",
            "range": "stddev: 0.07853315352443138",
            "extra": "mean: 1.10 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[no_modification-96-5000]",
            "value": 0.6077398546312113,
            "unit": "iter/sec",
            "range": "stddev: 0.006839882017761993",
            "extra": "mean: 1.65 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[individual_modification-96-5000]",
            "value": 0.5847084877082461,
            "unit": "iter/sec",
            "range": "stddev: 0.012014536051495833",
            "extra": "mean: 1.71 sec\nrounds: 5"
          }
        ]
      },
      {
        "commit": {
          "id": "40b42751446be4c1b477cb36286429a6967af16f",
          "message": "Add changelog for release 0.16.1 (#298)",
          "timestamp": "2026-01-22T10:27:50-05:00",
          "url": "https://github.com/Qiskit/samplomatic/commit/40b42751446be4c1b477cb36286429a6967af16f",
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
        "date": "2026-01-22T10:27:50-05:00",
        "tool": "pytest",
        "benches": [
          {
            "name": "test/performance/test_builder.py::TestBuilder::test_building_5k_circuit[96-5000]",
            "value": 0.20829429459967774,
            "unit": "iter/sec",
            "range": "stddev: 0.07408800147272306",
            "extra": "mean: 4.80 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.1379071586144855,
            "unit": "iter/sec",
            "range": "stddev: 0.02433438252179178",
            "extra": "mean: 7.25 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.08316129916569344,
            "unit": "iter/sec",
            "range": "stddev: 0.054398224091782535",
            "extra": "mean: 12.02 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.08322021102278919,
            "unit": "iter/sec",
            "range": "stddev: 0.0760221192346725",
            "extra": "mean: 12.02 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 1.5951296836928321,
            "unit": "iter/sec",
            "range": "stddev: 0.002586340911648449",
            "extra": "mean: 626.91 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 0.880521224623344,
            "unit": "iter/sec",
            "range": "stddev: 0.09075048607627946",
            "extra": "mean: 1.14 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[no_modification-96-5000]",
            "value": 0.5956179200057556,
            "unit": "iter/sec",
            "range": "stddev: 0.01105553020201682",
            "extra": "mean: 1.68 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[individual_modification-96-5000]",
            "value": 0.5851821647600688,
            "unit": "iter/sec",
            "range": "stddev: 0.016840514735909855",
            "extra": "mean: 1.71 sec\nrounds: 5"
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
            "value": 0.19250790101342025,
            "unit": "iter/sec",
            "range": "stddev: 0.07877122835195126",
            "extra": "mean: 5.19 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.1368339338603869,
            "unit": "iter/sec",
            "range": "stddev: 0.03290905902782006",
            "extra": "mean: 7.31 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.08196120206944538,
            "unit": "iter/sec",
            "range": "stddev: 0.0574095966668379",
            "extra": "mean: 12.20 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.08246907666095796,
            "unit": "iter/sec",
            "range": "stddev: 0.04980040486215505",
            "extra": "mean: 12.13 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 1.5817215423417914,
            "unit": "iter/sec",
            "range": "stddev: 0.006022363950618655",
            "extra": "mean: 632.22 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 0.8478364398651693,
            "unit": "iter/sec",
            "range": "stddev: 0.12047813025705066",
            "extra": "mean: 1.18 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialized_size[100-5000]",
            "value": 1.5842410292741986,
            "unit": "iter/sec",
            "range": "stddev: 0.0035808053512823316",
            "extra": "mean: 631.22 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[no_modification-96-5000]",
            "value": 0.46595230721358555,
            "unit": "iter/sec",
            "range": "stddev: 0.03056472309589741",
            "extra": "mean: 2.15 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[individual_modification-96-5000]",
            "value": 0.4457223963632555,
            "unit": "iter/sec",
            "range": "stddev: 0.012596196072619617",
            "extra": "mean: 2.24 sec\nrounds: 5"
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
            "value": 0.18866917521886287,
            "unit": "iter/sec",
            "range": "stddev: 0.1354039186533745",
            "extra": "mean: 5.30 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.13491225890203537,
            "unit": "iter/sec",
            "range": "stddev: 0.05796273480445385",
            "extra": "mean: 7.41 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.08304205055116534,
            "unit": "iter/sec",
            "range": "stddev: 0.06235994634475396",
            "extra": "mean: 12.04 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.08256219649832953,
            "unit": "iter/sec",
            "range": "stddev: 0.07000026233155923",
            "extra": "mean: 12.11 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 1.5980159351195569,
            "unit": "iter/sec",
            "range": "stddev: 0.002217947489887513",
            "extra": "mean: 625.78 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 0.8606555617855381,
            "unit": "iter/sec",
            "range": "stddev: 0.12706188209122626",
            "extra": "mean: 1.16 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialized_size[100-5000]",
            "value": 1.5865417662592118,
            "unit": "iter/sec",
            "range": "stddev: 0.0038342887924655354",
            "extra": "mean: 630.30 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[no_modification-96-5000]",
            "value": 0.4880633074748554,
            "unit": "iter/sec",
            "range": "stddev: 0.01997942070869264",
            "extra": "mean: 2.05 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[individual_modification-96-5000]",
            "value": 0.43625891428637537,
            "unit": "iter/sec",
            "range": "stddev: 0.07043498152020065",
            "extra": "mean: 2.29 sec\nrounds: 5"
          }
        ]
      }
    ]
  }
};
