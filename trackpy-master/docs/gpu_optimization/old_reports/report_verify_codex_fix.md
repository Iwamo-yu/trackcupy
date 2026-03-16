# 3D Locate GPU Benchmark Report: verify_codex_fix

## Environment

- timestamp: 2026-03-16T18:20:19
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

| scenario       | shape          |   count | diameter   |   noise_level |   seed | engine   | status               |   cold_ms |   steady_mean_ms |   steady_min_ms |   steady_max_ms |   steady_std_ms |   features |   speedup_vs_python |   speedup_vs_numba |
|:---------------|:---------------|--------:|:-----------|--------------:|-------:|:---------|:---------------------|----------:|-----------------:|----------------:|----------------:|----------------:|-----------:|--------------------:|-------------------:|
| iso_baseline   | (128, 128, 64) |     200 | (9, 9, 9)  |            20 |     42 | python   | ok                   |   205.11  |        196.274   |       189.827   |       203.383   |       4.95314   |        249 |             1       |           0.724251 |
| iso_baseline   | (128, 128, 64) |     200 | (9, 9, 9)  |            20 |     42 | numba    | ok                   |  1088.19  |        142.151   |       140.271   |       143.485   |       1.22669   |        249 |             1.38074 |           1        |
| iso_baseline   | (128, 128, 64) |     200 | (9, 9, 9)  |            20 |     42 | cupy     | FAIL_EMPTY_DETECTION |   427.594 |          7.31035 |         7.25383 |         7.40605 |       0.0567654 |          0 |            26.8487  |          19.4452   |
| iso_dense      | (128, 128, 64) |     500 | (9, 9, 9)  |            20 |     43 | python   | ok                   |   201.56  |        192.894   |       187.558   |       204.769   |       6.33533   |        248 |             1       |           0.715329 |
| iso_dense      | (128, 128, 64) |     500 | (9, 9, 9)  |            20 |     43 | numba    | ok                   |  1101.33  |        137.983   |       137.037   |       139.577   |       0.895439  |        248 |             1.39796 |           1        |
| iso_dense      | (128, 128, 64) |     500 | (9, 9, 9)  |            20 |     43 | cupy     | FAIL_EMPTY_DETECTION |   357.668 |          8.22996 |         8.16334 |         8.34602 |       0.0626923 |          0 |            23.4381  |          16.7659   |
| aniso_baseline | (128, 128, 64) |     200 | (7, 9, 9)  |            20 |     44 | python   | ok                   |   217.648 |        222.181   |       217.068   |       230.576   |       4.98292   |        296 |             1       |           0.627812 |
| aniso_baseline | (128, 128, 64) |     200 | (7, 9, 9)  |            20 |     44 | numba    | ok                   |  1181.98  |        139.488   |       137.175   |       144.975   |       2.95063   |        296 |             1.59283 |           1        |
| aniso_baseline | (128, 128, 64) |     200 | (7, 9, 9)  |            20 |     44 | cupy     | FAIL_EMPTY_DETECTION |   352.66  |          8.05983 |         7.94896 |         8.32298 |       0.136135  |          0 |            27.5664  |          17.3065   |
| iso_large      | (192, 192, 96) |     500 | (9, 9, 9)  |            20 |     45 | python   | ok                   |   710.897 |        698.403   |       690.468   |       719.174   |      10.6739    |        875 |             1       |           0.745292 |
| iso_large      | (192, 192, 96) |     500 | (9, 9, 9)  |            20 |     45 | numba    | ok                   |  1520.18  |        520.514   |       516.89    |       524.195   |       2.75863   |        875 |             1.34176 |           1        |
| iso_large      | (192, 192, 96) |     500 | (9, 9, 9)  |            20 |     45 | cupy     | FAIL_EMPTY_DETECTION |   378.441 |         42.2043  |        41.9784  |        42.6662  |       0.239407  |          0 |            16.5482  |          12.3332   |

## Accuracy

| scenario       | ref_engine   | engine   | status               |   ref_features |   target_features |   matched |   match_ratio_ref |   rmse_xyz |   mae_z |   mae_y |   mae_x |   mass_mare |   signal_mare |   raw_mass_mare |   size_mare |   size_z_mare |   size_y_mare |   size_x_mare |
|:---------------|:-------------|:---------|:---------------------|---------------:|------------------:|----------:|------------------:|-----------:|--------:|--------:|--------:|------------:|--------------:|----------------:|------------:|--------------:|--------------:|--------------:|
| iso_baseline   | python       | python   | ok                   |            249 |               249 |       249 |                 1 |          0 |       0 |       0 |       0 |           0 |             0 |               0 |           0 |           nan |           nan |           nan |
| iso_baseline   | python       | numba    | ok                   |            249 |               249 |       249 |                 1 |          0 |       0 |       0 |       0 |           0 |             0 |               0 |           0 |           nan |           nan |           nan |
| iso_baseline   | python       | cupy     | FAIL_EMPTY_DETECTION |            249 |                 0 |       nan |               nan |        nan |     nan |     nan |     nan |         nan |           nan |             nan |         nan |           nan |           nan |           nan |
| iso_dense      | python       | python   | ok                   |            248 |               248 |       248 |                 1 |          0 |       0 |       0 |       0 |           0 |             0 |               0 |           0 |           nan |           nan |           nan |
| iso_dense      | python       | numba    | ok                   |            248 |               248 |       248 |                 1 |          0 |       0 |       0 |       0 |           0 |             0 |               0 |           0 |           nan |           nan |           nan |
| iso_dense      | python       | cupy     | FAIL_EMPTY_DETECTION |            248 |                 0 |       nan |               nan |        nan |     nan |     nan |     nan |         nan |           nan |             nan |         nan |           nan |           nan |           nan |
| aniso_baseline | python       | python   | ok                   |            296 |               296 |       296 |                 1 |          0 |       0 |       0 |       0 |           0 |             0 |               0 |         nan |             0 |             0 |             0 |
| aniso_baseline | python       | numba    | ok                   |            296 |               296 |       296 |                 1 |          0 |       0 |       0 |       0 |           0 |             0 |               0 |         nan |             0 |             0 |             0 |
| aniso_baseline | python       | cupy     | FAIL_EMPTY_DETECTION |            296 |                 0 |       nan |               nan |        nan |     nan |     nan |     nan |         nan |           nan |             nan |         nan |           nan |           nan |           nan |
| iso_large      | python       | python   | ok                   |            875 |               875 |       875 |                 1 |          0 |       0 |       0 |       0 |           0 |             0 |               0 |           0 |           nan |           nan |           nan |
| iso_large      | python       | numba    | ok                   |            875 |               875 |       875 |                 1 |          0 |       0 |       0 |       0 |           0 |             0 |               0 |           0 |           nan |           nan |           nan |
| iso_large      | python       | cupy     | FAIL_EMPTY_DETECTION |            875 |                 0 |       nan |               nan |        nan |     nan |     nan |     nan |         nan |           nan |             nan |         nan |           nan |           nan |           nan |

## Speedup Assessment

- iso_baseline: MISS (FAIL_EMPTY_DETECTION)
- iso_dense: MISS (FAIL_EMPTY_DETECTION)
- aniso_baseline: MISS (FAIL_EMPTY_DETECTION)
- iso_large: MISS (FAIL_EMPTY_DETECTION)
