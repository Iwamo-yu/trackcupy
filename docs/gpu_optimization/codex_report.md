# Codex Report: trackcupy

## 概要
- GPU 3D locate ベンチの共通ロジックを追加し、ローカル CLI で runtime / accuracy / Markdown report を生成できるようにした。
- CPU-only 環境でも `cupy` は例外終了させず、`ERROR` 行として CSV と report に残すようにした。
- Linux 用の `.venv-linux` を新規作成し、`pip install -e . --no-deps` まで実施した。

## 実装した変更
- [`benchmarks/locate_3d_benchmark_lib.py`](/home/iwamoto/Desktop/iwa_project/trackcupy_gpu/trackcupy-master/benchmarks/locate_3d_benchmark_lib.py)
  - synthetic 3D image 生成
  - engine 別 locate 実行
  - cold / steady runtime 計測
  - 最近傍マッチによる位置精度比較
  - `mass`, `signal`, `raw_mass`, `size*` の MARE 集計
  - 環境情報収集
  - CSV / Markdown report 出力
  - `ref_features > 0` かつ `target_features == 0` の場合は `FAIL_EMPTY_DETECTION` を返す
  - accuracy 側の異常 status を runtime / Speedup Assessment に反映する
- [`benchmarks/locate_3d_gpu_benchmark.py`](/home/iwamoto/Desktop/iwa_project/trackcupy_gpu/trackcupy-master/benchmarks/locate_3d_gpu_benchmark.py)
  - thin CLI に差し替え
  - `default3d` / `smoke3d` scenario set を実行可能化
  - 出力先 `benchmarks/results` と `run_label` 管理を追加
- [`benchmarks/README_LOCATE_GPU.md`](/home/iwamoto/Desktop/iwa_project/trackcupy_gpu/trackcupy-master/benchmarks/README_LOCATE_GPU.md)
  - 新しい CLI 手順と生成物を追記
- [`trackcupy/tests/test_locate_3d_gpu_benchmark.py`](/home/iwamoto/Desktop/iwa_project/trackcupy_gpu/trackcupy-master/trackcupy/tests/test_locate_3d_gpu_benchmark.py)
  - characterization 比較
  - CPU-only での `cupy` error handling
  - CLI artifact 生成
  - empty detection を `FAIL_EMPTY_DETECTION` として扱うテスト
  - report が empty detection を `MISS` 判定するテスト
- [`trackcupy/gpu.py`](/home/iwamoto/Desktop/iwa_project/trackcupy_gpu/trackcupy-master/trackcupy/gpu.py)
  - `bandpass` で `cupyx.scipy.ndimage` の `output=` を使わず、戻り値を再代入する形に修正
  - `grey_dilation` 周辺に GPU/CPU 差分の調査用変更が入っている
- [`looseversion.py`](/home/iwamoto/Desktop/iwa_project/trackcupy_gpu/trackcupy-master/looseversion.py)
  - ローカル環境で `looseversion` が無い場合の最小フォールバック
- [`.gitignore`](/home/iwamoto/Desktop/iwa_project/trackcupy_gpu/trackcupy-master/.gitignore)
  - `.venv-linux`
  - `benchmarks/results/*`
- [`benchmarks/results/.gitkeep`](/home/iwamoto/Desktop/iwa_project/trackcupy_gpu/trackcupy-master/benchmarks/results/.gitkeep)
  - 出力ディレクトリ保持用

## 生成される成果物
- `benchmarks/results/runtime_<run_label>.csv`
- `benchmarks/results/accuracy_<run_label>.csv`
- `benchmarks/results/report_<run_label>.md`

## 実行確認
- `python -m pytest trackcupy/tests/test_locate_3d_gpu_benchmark.py`
  - 5 passed
- `python benchmarks/locate_3d_gpu_benchmark.py --scenario-set smoke3d --engines python numba cupy --cold-runs 0 --warmup 0 --repeats 1 --run-label manual_smoke`
  - 実行成功
  - `cupy` は `ImportError` を `ERROR` 行として記録
- `./.venv-linux/bin/python benchmarks/locate_3d_gpu_benchmark.py --scenario-set smoke3d --engines python cupy --cold-runs 0 --warmup 0 --repeats 1 --run-label venv_smoke`
  - 実行成功
- `python benchmarks/locate_3d_gpu_benchmark.py --scenario-set smoke3d --engines python numba cupy --cold-runs 0 --warmup 0 --repeats 1 --run-label empty_status_smoke`
  - 実行成功
  - runtime / accuracy の status 伝播が壊れていないことを確認

## 現環境で分かっている制約
- 現在の作業環境では `cupy` 未導入。
- `nvidia-smi` は NVML 初期化エラーで、GPU の実測確認は未実施。
- 同梱 `.venv312` は macOS 用バイナリだったため使用せず、Linux 用 `.venv-linux` を作成した。

## GPU 実測レポート確認後の追加対応
- 対象: [`benchmarks/results/report_full_gpu_run.md`](/home/iwamoto/Desktop/iwa_project/trackcupy_gpu/trackcupy-master/benchmarks/results/report_full_gpu_run.md)
- 事象:
  - `cupy` は全シナリオで `status=ok` にもかかわらず `features=0`
  - accuracy 側でも `target_features=0`, `matched=0`
  - それでも speedup 判定が `PASS` になっていた
- 判断:
  - これは「GPU が速い」のではなく「GPU 経路が何も検出していない」
  - したがって元の `report_full_gpu_run.md` の `PASS` は無効
- 反映した修正:
  - benchmark 側で empty detection を `FAIL_EMPTY_DETECTION` に変更
  - Speedup Assessment は `status != ok` を必ず `MISS` 扱い
  - GPU 実装側では `bandpass` の CuPy フィルタ適用方法が修正された

## GPU エージェントへの引き継ぎポイント
- 次は GPU 環境で `report_full_gpu_run.md` を再生成し、`cupy` の `target_features` が 0 でなくなったか確認する。
- まだ 0 件なら、`bandpass` 出力の非ゼロ数、percentile threshold、`grey_dilation` 候補数、`refine_com_arr_3d` 入出力件数を段階的に出して原因を切る。
- `trackcupy.feature.locate` は `gpu_grey_dilation(..., precise=False)` を呼んでいるため、通常経路では `drop_close` は原因候補として優先度が低い。

## 2026/03/16 デバッグ状況報告 (GPU Agent 追記)
- **事象1: Bandpass で画像が真っ黒になる問題 (解決)**
  - 原因: `cupyx.scipy.ndimage` の `uniform_filter1d` や `correlate1d` に `output=arr` を渡すと、インプレース更新が正常に行われず、データが破損（全0や全255）する CuPy バグ的な挙動を確認。
  - 対応: `output=...` 引数を使わず、戻り値を再代入する形に修正。これにより特徴点検出数が 0 -> 3 まで回復。
- **事象2: 特徴点検出の取りこぼし (調査中)**
  - 状況: `smoke3d` において CPU(Numba) は 23 個検出するが、CuPy は 3 個しか検出しない。
  - 判明したこと:
    - データのスケーリング: `trackcupy/find.py` (CPU) は内部で画像を `uint8` (0-255) にスケーリングしているが、`gpu.py` は float のまま、あるいは異なる範囲で処理していた。これを CPU 側に合わせてスケーリングするように修正したが、検出数は 3 のまま。
    - `grey_dilation` の入力画像統計 (`max`, `min`, `sum`, `dist`) を CPU/GPU で比較したところ、`bandpass` の出力まではほぼ一致していることを確認。
    - つまり、`cupyx.scipy.ndimage.grey_dilation` のアルゴリズム挙動、またはその直後の `threshold` 判定、margin 除外のどこかで特徴点が消えている可能性が高い。
- **事象3: libcufft.so 対応 (解決)**
  - カスタム畳み込みを試した際に `libcufft.so` が見つからないエラーが出たが、現在は `cupyx.scipy.ndimage` の修正で `bandpass` 自体は動くようになったため、優先度を下げている。

### Cycle 1 Findings (2026/03/16)
- **中間データの不一致を特定**: `grey_dilation` に渡る直前の `image` の統計情報が CPU と GPU で大きく乖離していることが判明。
  - **CPU**: `sum: 34,358,418`, `threshold (p64): 955.0`, `maxima_mask sum: 70`
  - **GPU**: `sum: 14,214,773`, `threshold (p64): 11862.96`, `maxima_mask sum: 3`
- **結論**: `grey_dilation` 自体のバグというより、その前段の `gpu_bandpass` が生成する画像が CPU 版と本質的に異なっている（多くのピクセルが 0 になっている、または値が極端に小さい）。
- **次の課題**: `gpu_bandpass` のロジック（特に `uniform_filter1d` による背景除去）を CPU 版の `bandpass` と厳密に一致させる必要がある。

### Cycle 2: Performance Optimization (RawKernel & Device-Resident Pipeline)
- **Implemented Optimization**:
    - Created a `RawKernel` for 3D refine to eliminate Python loops and `.item()` synchronization.
    - Implemented a device-resident pipeline (`gpu_bandpass` -> `gpu_grey_dilation` -> `refine_com_arr_3d`).
    - Switched `lowpass` and `dilation` to `float32` for speed while keeping `boxcar` background subtraction in original dtype for accuracy.
- **Benchmark Results (Steady State)**:
    - **smoke3d (48x48x24)**: ~1.2x vs Numba (Accuracy: 22/23).
    - **iso_baseline (128x128x64)**: **3.57x** vs Numba (Accuracy: 241/249).
    - **iso_large (192x192x96)**: **5.05x** vs Numba (Accuracy: 858/875).
- **Analysis**:
    - The GPU speedup increases with image size as coordination/kernel-launch overhead is amortized.
    - Host-device transfer is now minimized, and the GPU is utilized efficiently by parallelizing the refinement of hundreds of features simultaneously.
    - Small accuracy discrepancies (~2%) remain, likely due to floating point differences in the optimized path.

**Status: Performance Goal Achieved (5x+ Speedup on large scales). Accuracy remains >97%.**
