# 3D Locate GPU Benchmark Report: empty_status_smoke

## Environment

- timestamp: 2026-03-16T18:14:28
- python_executable: /home/iwamoto/anaconda3/bin/python
- python_version: 3.11.7
- platform: Linux-6.8.0-101-generic-x86_64-with-glibc2.35
- trackcupy_version: 0.7
- numpy_version: 1.26.4
- pandas_version: 2.0.3
- scipy_version: 1.11.4
- numba_version: 0.59.1
- cupy_version: ERROR: ModuleNotFoundError: No module named 'cupy'
- nvidia_smi: Failed to initialize NVML: Unknown Error

## Scenario Set

- name: `smoke3d`
- engines: `python, numba, cupy`
- speedup goal: `cupy >= 1.5x numba`

| scenario | shape | count | diameter | noise_level | seed |
| --- | --- | ---: | --- | ---: | ---: |
| smoke_iso | (48, 48, 24) | 8 | (7, 7, 7) | 10 | 123 |

## Runtime

| scenario   | shape        |   count | diameter   |   noise_level |   seed | engine   | status                                                                  |   cold_ms |   steady_mean_ms |   steady_min_ms |   steady_max_ms |   steady_std_ms |   features |   speedup_vs_python |   speedup_vs_numba |
|:-----------|:-------------|--------:|:-----------|--------------:|-------:|:---------|:------------------------------------------------------------------------|----------:|-----------------:|----------------:|----------------:|----------------:|-----------:|--------------------:|-------------------:|
| smoke_iso  | (48, 48, 24) |       8 | (7, 7, 7)  |            10 |    123 | python   | ok                                                                      |       nan |          17.8566 |         17.8566 |         17.8566 |               0 |         23 |           1         |            56.3916 |
| smoke_iso  | (48, 48, 24) |       8 | (7, 7, 7)  |            10 |    123 | numba    | ok                                                                      |       nan |        1006.97   |       1006.97   |       1006.97   |               0 |         23 |           0.0177331 |             1      |
| smoke_iso  | (48, 48, 24) |       8 | (7, 7, 7)  |            10 |    123 | cupy     | ERROR: ImportError: CuPy is required for trackcupy.locate(engine='cupy'). |       nan |         nan      |        nan      |        nan      |             nan |        nan |         nan         |           nan      |

## Accuracy

| scenario   | ref_engine   | engine   | status                                                                  |   ref_features |   target_features |   matched |   match_ratio_ref |   rmse_xyz |   mae_z |   mae_y |   mae_x |   mass_mare |   signal_mare |   raw_mass_mare |   size_mare |   size_z_mare |   size_y_mare |   size_x_mare |
|:-----------|:-------------|:---------|:------------------------------------------------------------------------|---------------:|------------------:|----------:|------------------:|-----------:|--------:|--------:|--------:|------------:|--------------:|----------------:|------------:|--------------:|--------------:|--------------:|
| smoke_iso  | python       | python   | ok                                                                      |             23 |                23 |        23 |                 1 |          0 |       0 |       0 |       0 |           0 |             0 |               0 |           0 |           nan |           nan |           nan |
| smoke_iso  | python       | numba    | ok                                                                      |             23 |                23 |        23 |                 1 |          0 |       0 |       0 |       0 |           0 |             0 |               0 |           0 |           nan |           nan |           nan |
| smoke_iso  | python       | cupy     | ERROR: ImportError: CuPy is required for trackcupy.locate(engine='cupy'). |             23 |               nan |       nan |               nan |        nan |     nan |     nan |     nan |         nan |           nan |             nan |         nan |           nan |           nan |           nan |

## Speedup Assessment

- smoke_iso: MISS (ERROR: ImportError: CuPy is required for trackcupy.locate(engine='cupy').)
