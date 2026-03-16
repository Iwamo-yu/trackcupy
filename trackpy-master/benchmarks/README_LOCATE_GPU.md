# 3D Locate GPU Benchmarks

このディレクトリには `trackcupy.locate` の3Dエンジン比較用アセットを置いています。

## ファイル構成
- `locate_3d_benchmark_lib.py`
  - ローカル CLI と今後の notebook 共通で使うベンチロジック
- `locate_3d_gpu_benchmark.py`
  - ローカル CLI で `python / numba / cupy` の実行時間と精度比較を出力
- `locate_3d_engine_benchmark_colab.ipynb`
  - Colab向けノートブック
  - 実行時間比較に加えて、検出結果比較（feature数、マッチ率、座標誤差）を出力

## ローカル実行例
```bash
python -m venv --system-site-packages .venv-linux
./.venv-linux/bin/python -m pip install -e . --no-deps
./.venv-linux/bin/python benchmarks/locate_3d_gpu_benchmark.py \
  --engines python numba cupy \
  --scenario-set default3d \
  --cold-runs 1 \
  --warmup 2 \
  --repeats 5 \
  --output-dir benchmarks/results
```

生成物:
- `benchmarks/results/runtime_<run_label>.csv`
- `benchmarks/results/accuracy_<run_label>.csv`
- `benchmarks/results/report_<run_label>.md`

## Colab実行
1. `benchmarks/locate_3d_engine_benchmark_colab.ipynb` をアップロード
2. ランタイムを GPU に変更
3. 上から順に実行
4. `Runtime` と `Detection` の表で比較

## 検出結果比較の定義
- 基準エンジン: `python`
- マッチング: 最近傍（`tol=1.0` px）
- 指標:
  - `ref_features` / `target_features`
  - `matched`
  - `match_ratio_ref`
  - `rmse_xyz`
  - `mae_z`, `mae_y`, `mae_x`
  - `mass_mare`, `signal_mare`, `raw_mass_mare`
  - `size_mare` または `size_z_mare`, `size_y_mare`, `size_x_mare`

## デフォルトシナリオ
- `iso_baseline`: `(128, 128, 64)`, count=`200`, diameter=`(9, 9, 9)`
- `iso_dense`: `(128, 128, 64)`, count=`500`, diameter=`(9, 9, 9)`
- `aniso_baseline`: `(128, 128, 64)`, count=`200`, diameter=`(7, 9, 9)`
- `iso_large`: `(192, 192, 96)`, count=`500`, diameter=`(9, 9, 9)`

## レポート判定
- `speedup_vs_numba >= 1.5` を `PASS`
- それ未満、または `cupy` 実行失敗時は `MISS`
