# 3D Locate GPU Benchmark Report: cycle2_optimized_scale

## Environment

- timestamp: 2026-03-16T21:14:33
- python_executable: /home/iwamoto/Desktop/iwa_project/trackcupy_gpu/trackcupy-master/.venv-gpu/bin/python
- python_version: 3.11.7
- platform: Linux-6.8.0-101-generic-x86_64-with-glibc2.35
- trackcupy_version: 0.7
- numpy_version: 2.4.3
- pandas_version: 3.0.1
- scipy_version: 1.17.1
- numba_version: 0.64.0
- cupy_version: 14.0.1
- nvidia_smi: NVIDIA GeForce RTX 4090, 570.211.01

## Scenario Set

- name: `default3d`
- engines: `numba, cupy`
- speedup goal: `cupy >= 1.5x numba`

| scenario | shape | count | diameter | noise_level | seed |
| --- | --- | ---: | --- | ---: | ---: |
| iso_baseline | (128, 128, 64) | 200 | (9, 9, 9) | 20 | 42 |
| iso_dense | (128, 128, 64) | 500 | (9, 9, 9) | 20 | 43 |
| aniso_baseline | (128, 128, 64) | 200 | (7, 9, 9) | 20 | 44 |
| iso_large | (192, 192, 96) | 500 | (9, 9, 9) | 20 | 45 |

## Runtime

| scenario       | shape          |   count | diameter   |   noise_level |   seed | engine   | status   |   cold_ms |   steady_mean_ms |   steady_min_ms |   steady_max_ms |   steady_std_ms |   features |   speedup_vs_python |   speedup_vs_numba |
|:---------------|:---------------|--------:|:-----------|--------------:|-------:|:---------|:---------|----------:|-----------------:|----------------:|----------------:|----------------:|-----------:|--------------------:|-------------------:|
| iso_baseline   | (128, 128, 64) |     200 | (9, 9, 9)  |            20 |     42 | numba    | ok       |  1093     |         145.923  |        144.136  |        150.798  |        2.52246  |        249 |                 nan |            1       |
| iso_baseline   | (128, 128, 64) |     200 | (9, 9, 9)  |            20 |     42 | cupy     | ok       |  4941.96  |          40.862  |         36.6861 |         44.6887 |        3.10052  |        241 |                 nan |            3.57112 |
| iso_dense      | (128, 128, 64) |     500 | (9, 9, 9)  |            20 |     43 | numba    | ok       |  1165.28  |         140.963  |        138.926  |        146.416  |        2.82671  |        248 |                 nan |            1       |
| iso_dense      | (128, 128, 64) |     500 | (9, 9, 9)  |            20 |     43 | cupy     | ok       |   473.309 |          36.2072 |         35.9991 |         36.4216 |        0.138489 |        238 |                 nan |            3.89323 |
| aniso_baseline | (128, 128, 64) |     200 | (7, 9, 9)  |            20 |     44 | numba    | ok       |  1132.49  |         140.08   |        138.685  |        142.183  |        1.65129  |        296 |                 nan |            1       |
| aniso_baseline | (128, 128, 64) |     200 | (7, 9, 9)  |            20 |     44 | cupy     | ok       |   480.116 |          35.1589 |         34.8033 |         35.3805 |        0.198195 |        290 |                 nan |            3.98419 |
| iso_large      | (192, 192, 96) |     500 | (9, 9, 9)  |            20 |     45 | numba    | ok       |  1513.66  |         514.95   |        512.17   |        518.196  |        2.0958   |        875 |                 nan |            1       |
| iso_large      | (192, 192, 96) |     500 | (9, 9, 9)  |            20 |     45 | cupy     | ok       |   570.456 |         101.867  |        101.484  |        102.14   |        0.22015  |        858 |                 nan |            5.0551  |

## Accuracy

| scenario       | ref_engine   | engine   | status   |   ref_features |   target_features |   matched |   match_ratio_ref |   rmse_xyz |   mae_z |   mae_y |   mae_x |   mass_mare |   signal_mare |   raw_mass_mare |   size_mare |   size_z_mare |   size_y_mare |   size_x_mare |
|:---------------|:-------------|:---------|:---------|---------------:|------------------:|----------:|------------------:|-----------:|--------:|--------:|--------:|------------:|--------------:|----------------:|------------:|--------------:|--------------:|--------------:|
| iso_baseline   | python       | numba    | ok       |            nan |               249 |       nan |               nan |        nan |     nan |     nan |     nan |         nan |           nan |             nan |         nan |           nan |           nan |           nan |
| iso_baseline   | python       | cupy     | ok       |            nan |               241 |       nan |               nan |        nan |     nan |     nan |     nan |         nan |           nan |             nan |         nan |           nan |           nan |           nan |
| iso_dense      | python       | numba    | ok       |            nan |               248 |       nan |               nan |        nan |     nan |     nan |     nan |         nan |           nan |             nan |         nan |           nan |           nan |           nan |
| iso_dense      | python       | cupy     | ok       |            nan |               238 |       nan |               nan |        nan |     nan |     nan |     nan |         nan |           nan |             nan |         nan |           nan |           nan |           nan |
| aniso_baseline | python       | numba    | ok       |            nan |               296 |       nan |               nan |        nan |     nan |     nan |     nan |         nan |           nan |             nan |         nan |           nan |           nan |           nan |
| aniso_baseline | python       | cupy     | ok       |            nan |               290 |       nan |               nan |        nan |     nan |     nan |     nan |         nan |           nan |             nan |         nan |           nan |           nan |           nan |
| iso_large      | python       | numba    | ok       |            nan |               875 |       nan |               nan |        nan |     nan |     nan |     nan |         nan |           nan |             nan |         nan |           nan |           nan |           nan |
| iso_large      | python       | cupy     | ok       |            nan |               858 |       nan |               nan |        nan |     nan |     nan |     nan |         nan |           nan |             nan |         nan |           nan |           nan |           nan |

## Speedup Assessment

- iso_baseline: PASS (speedup_vs_numba=3.571, status=ok)
- iso_dense: PASS (speedup_vs_numba=3.893, status=ok)
- aniso_baseline: PASS (speedup_vs_numba=3.984, status=ok)
- iso_large: PASS (speedup_vs_numba=5.055, status=ok)
