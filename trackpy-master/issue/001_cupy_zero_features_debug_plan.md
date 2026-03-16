# CuPy `0 features found` デバッグ・修正プラン

## 1. 問題の概要
GPUベンチマーク実行時、CuPyエンジンを使用したすべてのシナリオで特徴点の検出数が `0` となり、精度（Accuracy）が担保されない状態が判明しました。
同時に `trackpy/gpu.py:135: UserWarning: Image is completely black.` という警告が複数回発生します。

## 2. 初期のコード分析と原因の仮説
`UserWarning: Image is completely black.` は、`trackpy/gpu.py` の `grey_dilation` 関数において、処理対象の画像配列の非ゼロ要素がゼロ件（`image[cp.nonzero(image)].size == 0`）の場合にのみ発行されます。

このことから、**`grey_dilation` に画像が渡される前の前処理の段階（`bandpass` フィルタ処理後）で、画像データ全体が `0`（真っ黒）になってしまっている** 可能性が極めて高いです。具体的には以下の仮説が考えられます。

### 仮説1: `bandpass` での `threshold` ロジックの不備
`bandpass` 関数の最後で、以下のように閾値（`threshold`）による足切りが行われています。
```python
    result -= background
    result = cp.where(result >= threshold, result, 0)
```
入力データの型（整数か浮動小数点か）によって初期 `threshold` が `1` または `1/255.` に分岐しますが、Numpy版・Numba版とCuPy版での「型の解釈」の違いや、値域（0-255なのか0-1なのか）との不整合により、すべてが閾値未満と判定され `0` クリアされている可能性があります。

### 仮説2: `cupyx.scipy.ndimage` ライブラリの挙動の差異
バックグラウンド計算やたたみ込みに使われる `ndimage.uniform_filter1d` あるいは `ndimage.correlate1d` が、CuPy版ではSciPy版と異なるエッジ処理（境界でのNaNの伝播など）をしており、引き算の段階で画像が破壊されている可能性です。

### 仮説3: メモリホスト・デバイス間転送でのデータ欠損
`int`から`float`への `cp.array` でのキャスト時、または `cp.asnumpy()` での取り出し時に期待しない変換がかかっている可能性です。

## 3. デバッグと修正のステップ

### Step 1: `bandpass` の処理地点ごとの状態出力
`benchmarks/locate_3d_gpu_benchmark.py` を最小設定（`--scenario-set smoke3d`など）で実行しつつ、一時的に `trackpy/gpu.py` の `bandpass` 内部へデバッグ用の `print` 文を仕込みます。
- 元画像の最大値 `arr.max()`
- `background` 計算後の最大値
- `result -= background` 計算後の配列の最大値 / 最小値
- 適用される `threshold` の値

上記を出力し、**どの処理行の直後に配列がゼロ化（またはNaN化）しているか** をピンポイントで特定します。

### Step 2: Numpy (基準) と CuPy の中間配列のズレを検証
Step 1 で原因行が特定できたら、Numpy エンジンの `bandpass` と同じ値動きになっているべき時点での数値を比較します。型の判定に起因するものであれば `astype` や閾値判定ルーチンを Numpy と同等のふるまいに修正します。

### Step 3: `locate` バグ修正コミットの作成
原因が完全に特定できたら、`trackpy/gpu.py` を修正します。

### Step 4: ベンチマークによる精度の再確認
修正後、再度以下のコマンドを実行し、CuPy の `match_ratio_ref` が Python/Numba と同じく `1.0` (100%検出) に回復するか、そして維持されるべき速度（10倍以上のスピード）が落ちていないかを確認します。

```bash
uv run python benchmarks/locate_3d_gpu_benchmark.py --scenario-set default3d --engines python numba cupy --run-label debug_verify
```
