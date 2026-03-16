# 3D Locate GPU Benchmark Report: full_gpu_run

## Environment

- timestamp: 2026-03-16T18:05:43
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
- engines: `python, numba, cupy`
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
| iso_baseline   | (128, 128, 64) |     200 | (9, 9, 9)  |            20 |     42 | python   | ok       |   205.045 |        197.963   |       191.964   |       210.048   |       6.71513   |        249 |             1       |           0.732191 |
| iso_baseline   | (128, 128, 64) |     200 | (9, 9, 9)  |            20 |     42 | numba    | ok       |  1106.31  |        144.947   |       141.643   |       151.664   |       3.78862   |        249 |             1.36576 |           1        |
| iso_baseline   | (128, 128, 64) |     200 | (9, 9, 9)  |            20 |     42 | cupy     | ok       | 10110     |          6.94422 |         6.87532 |         6.97932 |       0.0388924 |          0 |            28.5076  |          20.873    |
| iso_dense      | (128, 128, 64) |     500 | (9, 9, 9)  |            20 |     43 | python   | ok       |   211.188 |        192.536   |       187.697   |       199.362   |       4.17443   |        248 |             1       |           0.714556 |
| iso_dense      | (128, 128, 64) |     500 | (9, 9, 9)  |            20 |     43 | numba    | ok       |  1144.59  |        137.578   |       136.873   |       139.73    |       1.08328   |        248 |             1.39947 |           1        |
| iso_dense      | (128, 128, 64) |     500 | (9, 9, 9)  |            20 |     43 | cupy     | ok       |   351.007 |          7.74265 |         7.54075 |         7.82486 |       0.102572  |          0 |            24.867   |          17.7689   |
| aniso_baseline | (128, 128, 64) |     200 | (7, 9, 9)  |            20 |     44 | python   | ok       |   226.136 |        204.114   |       200.761   |       213.354   |       4.67418   |        296 |             1       |           0.677818 |
| aniso_baseline | (128, 128, 64) |     200 | (7, 9, 9)  |            20 |     44 | numba    | ok       |  1144.71  |        138.352   |       137.272   |       140.514   |       1.21287   |        296 |             1.47532 |           1        |
| aniso_baseline | (128, 128, 64) |     200 | (7, 9, 9)  |            20 |     44 | cupy     | ok       |  1833.35  |          9.95069 |         9.89861 |         9.99047 |       0.0308434 |          0 |            20.5126  |          13.9038   |
| iso_large      | (192, 192, 96) |     500 | (9, 9, 9)  |            20 |     45 | python   | ok       |   698.365 |        709.597   |       691.541   |       729.962   |      13.0058    |        875 |             1       |           0.755785 |
| iso_large      | (192, 192, 96) |     500 | (9, 9, 9)  |            20 |     45 | numba    | ok       |  1486.22  |        536.303   |       523.978   |       544.109   |       8.01333   |        875 |             1.32313 |           1        |
| iso_large      | (192, 192, 96) |     500 | (9, 9, 9)  |            20 |     45 | cupy     | ok       |   380.317 |         49.9496  |        48.3516  |        50.908   |       0.861687  |          0 |            14.2063  |          10.7369   |

## Accuracy

| scenario       | ref_engine   | engine   | status   |   ref_features |   target_features |   matched |   match_ratio_ref |   rmse_xyz |   mae_z |   mae_y |   mae_x |   mass_mare |   signal_mare |   raw_mass_mare |   size_mare |   size_z_mare |   size_y_mare |   size_x_mare |
|:---------------|:-------------|:---------|:---------|---------------:|------------------:|----------:|------------------:|-----------:|--------:|--------:|--------:|------------:|--------------:|----------------:|------------:|--------------:|--------------:|--------------:|
| iso_baseline   | python       | python   | ok       |            249 |               249 |       249 |                 1 |          0 |       0 |       0 |       0 |           0 |             0 |               0 |           0 |           nan |           nan |           nan |
| iso_baseline   | python       | numba    | ok       |            249 |               249 |       249 |                 1 |          0 |       0 |       0 |       0 |           0 |             0 |               0 |           0 |           nan |           nan |           nan |
| iso_baseline   | python       | cupy     | ok       |            249 |                 0 |         0 |                 0 |        nan |     nan |     nan |     nan |         nan |           nan |             nan |         nan |           nan |           nan |           nan |
| iso_dense      | python       | python   | ok       |            248 |               248 |       248 |                 1 |          0 |       0 |       0 |       0 |           0 |             0 |               0 |           0 |           nan |           nan |           nan |
| iso_dense      | python       | numba    | ok       |            248 |               248 |       248 |                 1 |          0 |       0 |       0 |       0 |           0 |             0 |               0 |           0 |           nan |           nan |           nan |
| iso_dense      | python       | cupy     | ok       |            248 |                 0 |         0 |                 0 |        nan |     nan |     nan |     nan |         nan |           nan |             nan |         nan |           nan |           nan |           nan |
| aniso_baseline | python       | python   | ok       |            296 |               296 |       296 |                 1 |          0 |       0 |       0 |       0 |           0 |             0 |               0 |         nan |             0 |             0 |             0 |
| aniso_baseline | python       | numba    | ok       |            296 |               296 |       296 |                 1 |          0 |       0 |       0 |       0 |           0 |             0 |               0 |         nan |             0 |             0 |             0 |
| aniso_baseline | python       | cupy     | ok       |            296 |                 0 |         0 |                 0 |        nan |     nan |     nan |     nan |         nan |           nan |             nan |         nan |           nan |           nan |           nan |
| iso_large      | python       | python   | ok       |            875 |               875 |       875 |                 1 |          0 |       0 |       0 |       0 |           0 |             0 |               0 |           0 |           nan |           nan |           nan |
| iso_large      | python       | numba    | ok       |            875 |               875 |       875 |                 1 |          0 |       0 |       0 |       0 |           0 |             0 |               0 |           0 |           nan |           nan |           nan |
| iso_large      | python       | cupy     | ok       |            875 |                 0 |         0 |                 0 |        nan |     nan |     nan |     nan |         nan |           nan |             nan |         nan |           nan |           nan |           nan |

## Speedup Assessment

- iso_baseline: PASS (speedup_vs_numba=20.873, status=ok)
- iso_dense: PASS (speedup_vs_numba=17.769, status=ok)
- aniso_baseline: PASS (speedup_vs_numba=13.904, status=ok)
- iso_large: PASS (speedup_vs_numba=10.737, status=ok)
