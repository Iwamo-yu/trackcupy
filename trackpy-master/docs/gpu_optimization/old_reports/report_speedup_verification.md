# 3D Locate GPU Benchmark Report: speedup_verification

## Environment

- timestamp: 2026-03-16T20:50:35
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
| iso_baseline   | (128, 128, 64) |     200 | (9, 9, 9)  |            20 |     42 | numba    | ok       |   1099.52 |          141.921 |         140.929 |         143.5   |        0.985384 |        249 |                 nan |           1        |
| iso_baseline   | (128, 128, 64) |     200 | (9, 9, 9)  |            20 |     42 | cupy     | ok       |   9825.85 |          735.574 |         733.804 |         737.01  |        1.2683   |        241 |                 nan |           0.192939 |
| iso_dense      | (128, 128, 64) |     500 | (9, 9, 9)  |            20 |     43 | numba    | ok       |   1130.39 |          142.25  |         137.499 |         146.933 |        3.86772  |        248 |                 nan |           1        |
| iso_dense      | (128, 128, 64) |     500 | (9, 9, 9)  |            20 |     43 | cupy     | ok       |   1268.87 |          740.492 |         735.892 |         747.321 |        3.86056  |        238 |                 nan |           0.192102 |
| aniso_baseline | (128, 128, 64) |     200 | (7, 9, 9)  |            20 |     44 | numba    | ok       |   1104.09 |          138.13  |         137.629 |         139.35  |        0.625262 |        296 |                 nan |           1        |
| aniso_baseline | (128, 128, 64) |     200 | (7, 9, 9)  |            20 |     44 | cupy     | ok       |   1573.96 |         1114.75  |        1099.71  |        1122.61  |        8.73231  |        290 |                 nan |           0.123911 |
| iso_large      | (192, 192, 96) |     500 | (9, 9, 9)  |            20 |     45 | numba    | ok       |   1489.88 |          521.717 |         515.5   |         536.187 |        7.44294  |        875 |                 nan |           1        |
| iso_large      | (192, 192, 96) |     500 | (9, 9, 9)  |            20 |     45 | cupy     | ok       |   3282.42 |         2629.93  |        2623.89  |        2636.54  |        5.5189   |        856 |                 nan |           0.198376 |

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
| iso_large      | python       | cupy     | ok       |            nan |               856 |       nan |               nan |        nan |     nan |     nan |     nan |         nan |           nan |             nan |         nan |           nan |           nan |           nan |

## Speedup Assessment

- iso_baseline: MISS (speedup_vs_numba=0.193, status=ok)
- iso_dense: MISS (speedup_vs_numba=0.192, status=ok)
- aniso_baseline: MISS (speedup_vs_numba=0.124, status=ok)
- iso_large: MISS (speedup_vs_numba=0.198, status=ok)
