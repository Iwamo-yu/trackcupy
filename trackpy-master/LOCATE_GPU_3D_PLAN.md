# trackpy.locate 3D GPU高速化 計画

## 概要
`trackpy.locate` の3D処理をGPUで高速化しつつ、既存の `python` / `numba` 経路との互換性を維持する。  
成功条件は以下。

- 3Dの主要テストが通る
- GPU有効時にCPUより有意な性能向上が出る
- GPU未導入環境で後方互換を保つ

## 実装方針（段階導入）

### 1. API拡張（互換維持）
- `engine` に `cupy` を追加（`{'auto', 'python', 'numba', 'cupy'}`）
- `auto` は既存挙動優先（従来どおり）
- 明示的に `engine='cupy'` を指定したときのみGPU経路へ
- `cupy` 指定かつCuPy未導入時は明示的エラー

### 2. GPU基盤レイヤの追加
- `trackpy/gpu.py`（新規）を追加し、以下を集約
  - CuPy/CuPyX の遅延import
  - `asnumpy` / `asarray` ヘルパ
  - CUDA利用可否チェック
- 依存は optional のまま（必須依存は増やさない）

### 3. 3D locateパイプラインGPU化
`locate` の主要3段をGPU対応。

- 前処理: `bandpass` 相当（`cupyx.scipy.ndimage` ベース）
- 極大検出: `grey_dilation` 相当（dilation + percentile threshold + margin除外）
- 近接重複除去: 当面CPU（候補座標のみCPUへ転送）

戻り値は従来どおりCPU側の `pandas.DataFrame` に統一する。

### 4. refine_com_arr の `cupy` エンジン追加（3D優先）
- `trackpy/refine/center_of_mass.py` に `engine == 'cupy'` を追加
- 3D向けにGPUカーネルで COM 反復と以下を計算
  - 座標
  - `mass`
  - `size` / `size_*`
  - `signal`
  - `raw_mass`
- 2Dは初期段階ではCPUフォールバック可（3D最優先）

### 5. ドキュメント更新
- `trackpy.locate` / `trackpy.refine_com` docstringに `cupy` を追記
- `doc/api.rst` にGPU engine（experimental）節を追加
  - 導入方法
  - 制約
  - 3D利用時の推奨条件

## テスト計画

### 1. 機能同等性
- `trackpy/tests/test_feature.py` に `TestFeatureIdentificationWithCuPy` を追加
- 既存 `CommonFeatureIdentificationTests` を再利用
- 3D重点テスト
  - `test_one_centered_gaussian_3D`
  - `test_one_centered_gaussian_3D_anisotropic`
  - `test_multiple_anisotropic_3D_simple`
- CuPy未導入環境では `SkipTest`

### 2. 数値許容差
- 座標: `atol=0.1~0.2`
- `mass` / `size` / `signal` / `raw_mass`: `rtol=0.05~0.1`
- anisotropic 3D の `size_*` 列の存在と比率妥当性を検証

### 3. 互換性確認
- 既存 `python` / `numba` テストが無変更で通ること
- `engine='cupy'` 指定時の未導入エラー文言テストを追加

### 4. 性能検証
- `benchmarks/` に3D locateベンチを追加
  - 例: `128x128x64`、粒子密度を複数条件
- 計測項目
  - エンドツーエンド時間
  - 前処理 / 極大検出 / refine の内訳
  - 初回ウォームアップと定常時を分離
- 目標: 定常時でCPU numba比 1.5x 以上

## 前提・デフォルト
- 対象GPUは NVIDIA + CuPy 前提
- `batch` は `locate` 経由で自然対応とする（別API追加なし）
- 初期リリースの `engine='cupy'` は experimental 扱い
- 破壊的変更は行わない

## ベンチ資産の配置
- ローカル実行: `benchmarks/locate_3d_gpu_benchmark.py`
- Colab実行: `benchmarks/locate_3d_engine_benchmark_colab.ipynb`
- 使い方/指標定義: `benchmarks/README_LOCATE_GPU.md`

## PR単位の分割（Step 1〜5）

### Step 1: API/基盤の導入（機能はまだCPUフォールバック）
**目的**  
`engine='cupy'` を安全に受け付ける土台を作る。

**変更**  
- `trackpy/gpu.py` 新規追加（遅延import、利用可否チェック、`asnumpy`/`asarray`）
- `trackpy/feature.py` の `locate` docstring/引数バリデーション更新
- `trackpy/refine/center_of_mass.py` の `engine` バリデーション更新

**DoD**  
- `engine='cupy'` が未導入環境で明示エラーを返す
- 既存 `python`/`numba` 挙動が不変

**テスト**  
- `pytest trackpy/tests/test_feature.py -k "engine or smoke"`

### Step 2: 3D前処理・極大検出のGPU化
**目的**  
`locate` の前半（`bandpass` + `grey_dilation`）をGPU実行可能にする。

**変更**  
- GPU版 `bandpass` ヘルパ追加（`cupyx.scipy.ndimage`）
- GPU版 `grey_dilation` ヘルパ追加
- `locate` で `engine='cupy'` 時に前半をGPU経路へ
- 近接重複除去はCPUの `where_close` を暫定利用

**DoD**  
- 3D画像で座標候補が取得できる
- CPU経路との差分が許容範囲内

**テスト**  
- `pytest trackpy/tests/test_feature.py -k "maxima or 3D"`

### Step 3: 3D refineのGPU化（コア高速化）
**目的**  
`refine_com_arr` の3D計算をGPU化し、実効速度を出す。

**変更**  
- `trackpy/refine/center_of_mass.py` に `engine='cupy'` 実装追加
- 3D COM反復、`mass/size/signal/raw_mass` をGPUカーネルで算出
- 結果列構成を既存 `numba` 3Dと一致させる

**DoD**  
- `locate(..., engine='cupy')` が3Dで最後まで実行できる
- 既存3D精度テストに通る

**テスト**  
- `pytest trackpy/tests/test_feature.py -k "3D or anisotropic"`

### Step 4: CuPy専用テスト整備と誤差境界の固定
**目的**  
GPU経路の回帰検知を可能にする。

**変更**  
- `trackpy/tests/test_feature.py` に `TestFeatureIdentificationWithCuPy` 追加
- CuPy未導入時の `SkipTest` を実装
- 数値誤差境界（`atol`/`rtol`）をテストとして固定

**DoD**  
- GPU環境でCuPyテストが安定して通る
- 非GPU環境でスキップ動作が安定

**テスト**  
- `pytest trackpy/tests/test_feature.py -k "CuPy or cupy"`
- `pytest trackpy/tests/test_feature.py`

### Step 5: ベンチマーク・ドキュメント・リリース準備
**目的**  
性能根拠と利用条件を明文化し、マージ可能状態にする。

**変更**  
- `benchmarks/` に3D locateベンチ追加
- `doc/api.rst` と対象docstring更新（experimental表記）
- 制約（NVIDIA/CuPy、初回ウォームアップ）を明記

**DoD**  
- 定常時でCPU numba比 1.5x以上（目標）
- ドキュメントのみで利用開始できる

**テスト/計測**  
- `pytest trackpy/tests/test_feature.py`
- ベンチ実行結果をPR本文に添付（条件・サイズ・反復回数込み）
