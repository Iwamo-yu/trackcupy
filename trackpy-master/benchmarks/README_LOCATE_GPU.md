# 3D Locate GPU Benchmarks

このディレクトリには `trackpy.locate` の3Dエンジン比較用アセットを置いています。

## ファイル構成
- `locate_3d_gpu_benchmark.py`
  - ローカルCLIで `python / numba / cupy` の実行時間を比較するスクリプト
- `locate_3d_engine_benchmark_colab.ipynb`
  - Colab向けノートブック
  - 実行時間比較に加えて、検出結果比較（feature数、マッチ率、座標誤差）を出力

## ローカル実行例
```bash
./.venv312/bin/python benchmarks/locate_3d_gpu_benchmark.py \
  --engines python numba cupy \
  --shape 128 128 64 \
  --count 200 \
  --diameter 9 9 9 \
  --warmup 2 \
  --repeats 5
```

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
