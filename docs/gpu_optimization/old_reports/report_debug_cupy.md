# 3D Locate GPU Benchmark Report: debug_cupy

## Environment

- timestamp: 2026-03-16T18:28:37
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

- name: `smoke3d`
- engines: `numba, cupy`
- speedup goal: `cupy >= 1.5x numba`

| scenario | shape | count | diameter | noise_level | seed |
| --- | --- | ---: | --- | ---: | ---: |
| smoke_iso | (48, 48, 24) | 8 | (7, 7, 7) | 10 | 123 |

## Runtime

| scenario   | shape        |   count | diameter   |   noise_level |   seed | engine   | status   |   cold_ms |   steady_mean_ms |   steady_min_ms |   steady_max_ms |   steady_std_ms |   features |   speedup_vs_python |   speedup_vs_numba |
|:-----------|:-------------|--------:|:-----------|--------------:|-------:|:---------|:---------|----------:|-----------------:|----------------:|----------------:|----------------:|-----------:|--------------------:|-------------------:|
| smoke_iso  | (48, 48, 24) |       8 | (7, 7, 7)  |            10 |    123 | numba    | ok       |   974.868 |          10.0897 |         9.79007 |         10.4183 |        0.215111 |         23 |                 nan |           1        |
| smoke_iso  | (48, 48, 24) |       8 | (7, 7, 7)  |            10 |    123 | cupy     | ok       |  5079.06  |          25.4805 |        19.7274  |         31.9959 |        4.73037  |          3 |                 nan |           0.395976 |

## Accuracy

| scenario   | ref_engine   | engine   | status   |   ref_features |   target_features |   matched |   match_ratio_ref |   rmse_xyz |   mae_z |   mae_y |   mae_x |   mass_mare |   signal_mare |   raw_mass_mare |   size_mare |   size_z_mare |   size_y_mare |   size_x_mare |
|:-----------|:-------------|:---------|:---------|---------------:|------------------:|----------:|------------------:|-----------:|--------:|--------:|--------:|------------:|--------------:|----------------:|------------:|--------------:|--------------:|--------------:|
| smoke_iso  | python       | numba    | ok       |            nan |                23 |       nan |               nan |        nan |     nan |     nan |     nan |         nan |           nan |             nan |         nan |           nan |           nan |           nan |
| smoke_iso  | python       | cupy     | ok       |            nan |                 3 |       nan |               nan |        nan |     nan |     nan |     nan |         nan |           nan |             nan |         nan |           nan |           nan |           nan |

## Speedup Assessment

- smoke_iso: MISS (speedup_vs_numba=0.396, status=ok)
