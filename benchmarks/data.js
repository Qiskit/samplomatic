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
            "value": 0.14158239317531057,
            "unit": "iter/sec",
            "range": "stddev: 0.18341680218912437",
            "extra": "mean: 7.06 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[1650-5000-100]",
            "value": 0.13492560734346581,
            "unit": "iter/sec",
            "range": "stddev: 0.07310469135700447",
            "extra": "mean: 7.41 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-1650-5000-100]",
            "value": 0.11081390222170155,
            "unit": "iter/sec",
            "range": "stddev: 0.07188402045971316",
            "extra": "mean: 9.02 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-1650-5000-100]",
            "value": 0.11156689730288522,
            "unit": "iter/sec",
            "range": "stddev: 0.065274660303482",
            "extra": "mean: 8.96 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[5000-100]",
            "value": 9.178862920141828,
            "unit": "iter/sec",
            "range": "stddev: 0.033334540839670454",
            "extra": "mean: 108.95 msec\nrounds: 11"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[5000-100]",
            "value": 4.169033440847924,
            "unit": "iter/sec",
            "range": "stddev: 0.05255251683689332",
            "extra": "mean: 239.86 msec\nrounds: 5"
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
            "value": 0.13531448218227812,
            "unit": "iter/sec",
            "range": "stddev: 0.1298389684896437",
            "extra": "mean: 7.39 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.13521523816613623,
            "unit": "iter/sec",
            "range": "stddev: 0.047242182694310866",
            "extra": "mean: 7.40 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.10942517122147007,
            "unit": "iter/sec",
            "range": "stddev: 0.08371602644028076",
            "extra": "mean: 9.14 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.10101681431207953,
            "unit": "iter/sec",
            "range": "stddev: 0.0457818594127461",
            "extra": "mean: 9.90 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 7.06957652467341,
            "unit": "iter/sec",
            "range": "stddev: 0.04486794955721923",
            "extra": "mean: 141.45 msec\nrounds: 11"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 4.992531613712471,
            "unit": "iter/sec",
            "range": "stddev: 0.0013024461221170795",
            "extra": "mean: 200.30 msec\nrounds: 6"
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
            "value": 0.1378478617754943,
            "unit": "iter/sec",
            "range": "stddev: 0.22363187910842905",
            "extra": "mean: 7.25 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.1343007877814384,
            "unit": "iter/sec",
            "range": "stddev: 0.05082213161435474",
            "extra": "mean: 7.45 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.12900599825936038,
            "unit": "iter/sec",
            "range": "stddev: 0.0741420820807559",
            "extra": "mean: 7.75 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.12981788699148833,
            "unit": "iter/sec",
            "range": "stddev: 0.06589164051807554",
            "extra": "mean: 7.70 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 7.928174407014138,
            "unit": "iter/sec",
            "range": "stddev: 0.03954368518614909",
            "extra": "mean: 126.13 msec\nrounds: 11"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 5.0471995002008265,
            "unit": "iter/sec",
            "range": "stddev: 0.001316351662226363",
            "extra": "mean: 198.13 msec\nrounds: 6"
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
            "value": 0.14256250131062653,
            "unit": "iter/sec",
            "range": "stddev: 0.08988504664848786",
            "extra": "mean: 7.01 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.1368687056566257,
            "unit": "iter/sec",
            "range": "stddev: 0.044922000131526106",
            "extra": "mean: 7.31 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.1303092592153761,
            "unit": "iter/sec",
            "range": "stddev: 0.043260638326346905",
            "extra": "mean: 7.67 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.12962847254235876,
            "unit": "iter/sec",
            "range": "stddev: 0.09721438394438968",
            "extra": "mean: 7.71 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 8.842529980116424,
            "unit": "iter/sec",
            "range": "stddev: 0.03552699970294766",
            "extra": "mean: 113.09 msec\nrounds: 11"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 4.974950898354562,
            "unit": "iter/sec",
            "range": "stddev: 0.002523381913377331",
            "extra": "mean: 201.01 msec\nrounds: 5"
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
            "value": 0.13999045288461656,
            "unit": "iter/sec",
            "range": "stddev: 0.1261140454843355",
            "extra": "mean: 7.14 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.13679041711029755,
            "unit": "iter/sec",
            "range": "stddev: 0.054529912175571627",
            "extra": "mean: 7.31 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.13004239007966711,
            "unit": "iter/sec",
            "range": "stddev: 0.06956297633387389",
            "extra": "mean: 7.69 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.12925839667691183,
            "unit": "iter/sec",
            "range": "stddev: 0.029005502141129416",
            "extra": "mean: 7.74 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 8.36237123666599,
            "unit": "iter/sec",
            "range": "stddev: 0.04027994852298475",
            "extra": "mean: 119.58 msec\nrounds: 11"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 4.4344864680610065,
            "unit": "iter/sec",
            "range": "stddev: 0.0339880038518505",
            "extra": "mean: 225.51 msec\nrounds: 5"
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
            "value": 0.1401821515314771,
            "unit": "iter/sec",
            "range": "stddev: 0.1433779270389731",
            "extra": "mean: 7.13 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.13647685959862346,
            "unit": "iter/sec",
            "range": "stddev: 0.04013058268135843",
            "extra": "mean: 7.33 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.13075239563148086,
            "unit": "iter/sec",
            "range": "stddev: 0.060894847923618156",
            "extra": "mean: 7.65 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.12967931738493454,
            "unit": "iter/sec",
            "range": "stddev: 0.08053695571276344",
            "extra": "mean: 7.71 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 8.16285217190793,
            "unit": "iter/sec",
            "range": "stddev: 0.03858531083414676",
            "extra": "mean: 122.51 msec\nrounds: 11"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 5.123331241888076,
            "unit": "iter/sec",
            "range": "stddev: 0.0015461504355223769",
            "extra": "mean: 195.19 msec\nrounds: 6"
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
            "value": 0.13800572860051738,
            "unit": "iter/sec",
            "range": "stddev: 0.3185839120218187",
            "extra": "mean: 7.25 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.13609392881044474,
            "unit": "iter/sec",
            "range": "stddev: 0.07496956165087042",
            "extra": "mean: 7.35 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.13138942715795726,
            "unit": "iter/sec",
            "range": "stddev: 0.03671614845287663",
            "extra": "mean: 7.61 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.1295423779332337,
            "unit": "iter/sec",
            "range": "stddev: 0.05810484735403487",
            "extra": "mean: 7.72 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 7.754218396842712,
            "unit": "iter/sec",
            "range": "stddev: 0.04255784493280555",
            "extra": "mean: 128.96 msec\nrounds: 11"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 5.077123653380376,
            "unit": "iter/sec",
            "range": "stddev: 0.0015633355704101361",
            "extra": "mean: 196.96 msec\nrounds: 6"
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
            "value": 0.13992140268701506,
            "unit": "iter/sec",
            "range": "stddev: 0.25648082423061",
            "extra": "mean: 7.15 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.13694504093584497,
            "unit": "iter/sec",
            "range": "stddev: 0.03459594627650346",
            "extra": "mean: 7.30 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.13070325936339441,
            "unit": "iter/sec",
            "range": "stddev: 0.07741874185408734",
            "extra": "mean: 7.65 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.13028025281322117,
            "unit": "iter/sec",
            "range": "stddev: 0.03746959251391077",
            "extra": "mean: 7.68 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 1.587000640087674,
            "unit": "iter/sec",
            "range": "stddev: 0.000814712958014874",
            "extra": "mean: 630.12 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 0.8528733339036775,
            "unit": "iter/sec",
            "range": "stddev: 0.12508755500743451",
            "extra": "mean: 1.17 sec\nrounds: 5"
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
            "value": 0.14382339755141807,
            "unit": "iter/sec",
            "range": "stddev: 0.08348622878155593",
            "extra": "mean: 6.95 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.13649394663566838,
            "unit": "iter/sec",
            "range": "stddev: 0.05051046243036964",
            "extra": "mean: 7.33 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.13159888033914194,
            "unit": "iter/sec",
            "range": "stddev: 0.06882593392936323",
            "extra": "mean: 7.60 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.13103519082326837,
            "unit": "iter/sec",
            "range": "stddev: 0.08027040350009769",
            "extra": "mean: 7.63 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 1.605646103205866,
            "unit": "iter/sec",
            "range": "stddev: 0.0011209881827387923",
            "extra": "mean: 622.80 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 0.8639002199447805,
            "unit": "iter/sec",
            "range": "stddev: 0.08434778854168033",
            "extra": "mean: 1.16 sec\nrounds: 5"
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
            "value": 0.1414225482126674,
            "unit": "iter/sec",
            "range": "stddev: 0.11249232228882725",
            "extra": "mean: 7.07 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.13958300000400742,
            "unit": "iter/sec",
            "range": "stddev: 0.05822450829976575",
            "extra": "mean: 7.16 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.13344485195062353,
            "unit": "iter/sec",
            "range": "stddev: 0.09081772675213072",
            "extra": "mean: 7.49 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.1320934077188512,
            "unit": "iter/sec",
            "range": "stddev: 0.081636146540283",
            "extra": "mean: 7.57 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 1.5431066769976887,
            "unit": "iter/sec",
            "range": "stddev: 0.006051101407519471",
            "extra": "mean: 648.04 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 0.8481152372738303,
            "unit": "iter/sec",
            "range": "stddev: 0.0773985174670121",
            "extra": "mean: 1.18 sec\nrounds: 5"
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
            "value": 0.18725238255194143,
            "unit": "iter/sec",
            "range": "stddev: 0.040328881512328656",
            "extra": "mean: 5.34 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.13687621810519543,
            "unit": "iter/sec",
            "range": "stddev: 0.037421294988606545",
            "extra": "mean: 7.31 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.13036514312722416,
            "unit": "iter/sec",
            "range": "stddev: 0.0547313457366231",
            "extra": "mean: 7.67 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.13156200032013649,
            "unit": "iter/sec",
            "range": "stddev: 0.051342655404393554",
            "extra": "mean: 7.60 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 1.588129706697182,
            "unit": "iter/sec",
            "range": "stddev: 0.0032963170158748266",
            "extra": "mean: 629.67 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 0.8723536029862021,
            "unit": "iter/sec",
            "range": "stddev: 0.08379938705164619",
            "extra": "mean: 1.15 sec\nrounds: 5"
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
            "value": 0.20094989130169164,
            "unit": "iter/sec",
            "range": "stddev: 0.13946094535457573",
            "extra": "mean: 4.98 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.13752602246733933,
            "unit": "iter/sec",
            "range": "stddev: 0.05492324649066974",
            "extra": "mean: 7.27 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.0834170480105909,
            "unit": "iter/sec",
            "range": "stddev: 0.07337295774127368",
            "extra": "mean: 11.99 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.08260641159459024,
            "unit": "iter/sec",
            "range": "stddev: 0.08517471686261414",
            "extra": "mean: 12.11 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 1.5725049032306604,
            "unit": "iter/sec",
            "range": "stddev: 0.004902971117762718",
            "extra": "mean: 635.93 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 0.8668986410912208,
            "unit": "iter/sec",
            "range": "stddev: 0.08747390085421498",
            "extra": "mean: 1.15 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[no_modification-96-5000]",
            "value": 0.5845077246267717,
            "unit": "iter/sec",
            "range": "stddev: 0.007033556493023018",
            "extra": "mean: 1.71 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[individual_modification-96-5000]",
            "value": 0.5297812733136027,
            "unit": "iter/sec",
            "range": "stddev: 0.028399919093115657",
            "extra": "mean: 1.89 sec\nrounds: 5"
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
            "value": 0.20378941700339362,
            "unit": "iter/sec",
            "range": "stddev: 0.08843969542777615",
            "extra": "mean: 4.91 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.13644029461755017,
            "unit": "iter/sec",
            "range": "stddev: 0.02124089705464447",
            "extra": "mean: 7.33 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.08242218552319627,
            "unit": "iter/sec",
            "range": "stddev: 0.07087005574073231",
            "extra": "mean: 12.13 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.08244855189802963,
            "unit": "iter/sec",
            "range": "stddev: 0.08935654793623096",
            "extra": "mean: 12.13 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 1.5822260672708195,
            "unit": "iter/sec",
            "range": "stddev: 0.0022239114239146524",
            "extra": "mean: 632.02 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 0.8465841328025443,
            "unit": "iter/sec",
            "range": "stddev: 0.06398799381723907",
            "extra": "mean: 1.18 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[no_modification-96-5000]",
            "value": 0.5733135186258844,
            "unit": "iter/sec",
            "range": "stddev: 0.012204402310020596",
            "extra": "mean: 1.74 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[individual_modification-96-5000]",
            "value": 0.5493935473947259,
            "unit": "iter/sec",
            "range": "stddev: 0.038049523792708",
            "extra": "mean: 1.82 sec\nrounds: 5"
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
            "value": 0.2023443423602391,
            "unit": "iter/sec",
            "range": "stddev: 0.1498761555305761",
            "extra": "mean: 4.94 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_5k_circuit[96-5000-1650]",
            "value": 0.13957735726655596,
            "unit": "iter/sec",
            "range": "stddev: 0.06034751499795206",
            "extra": "mean: 7.16 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_noisy_circuit[-1.0-96-5000-1650]",
            "value": 0.08444129036251755,
            "unit": "iter/sec",
            "range": "stddev: 0.06396416729384741",
            "extra": "mean: 11.84 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_sampling.py::TestSample::test_sampling_masked_noisy_circuit[2.0-96-5000-1650]",
            "value": 0.08398667464799689,
            "unit": "iter/sec",
            "range": "stddev: 0.10742537704691552",
            "extra": "mean: 11.91 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_serialize_noisy_circuit[100-5000]",
            "value": 1.599012647809791,
            "unit": "iter/sec",
            "range": "stddev: 0.004104331270174221",
            "extra": "mean: 625.39 msec\nrounds: 5"
          },
          {
            "name": "test/performance/test_serialization.py::test_deserialize_noisy_circuit[100-5000]",
            "value": 0.8951707881686639,
            "unit": "iter/sec",
            "range": "stddev: 0.07176299612851494",
            "extra": "mean: 1.12 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[no_modification-96-5000]",
            "value": 0.5772287017818915,
            "unit": "iter/sec",
            "range": "stddev: 0.05054737836694647",
            "extra": "mean: 1.73 sec\nrounds: 5"
          },
          {
            "name": "test/performance/test_transpiler.py::test_transpiling_5k_circuit[individual_modification-96-5000]",
            "value": 0.5750234371703922,
            "unit": "iter/sec",
            "range": "stddev: 0.0068904969761051215",
            "extra": "mean: 1.74 sec\nrounds: 5"
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
