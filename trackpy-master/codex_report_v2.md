# Codex Report V2

## 目的
- GPU agent に渡す前に、こちらで確定的に直せる箇所を整理して反映する。
- 実コードと引き継ぎ文書の不一致をなくす。
- 未解決の GPU 検出不良は、原因候補を絞った状態で handoff する。

## 今回反映した修正
- [`trackpy/gpu.py`](/home/iwamoto/Desktop/iwa_project/trackpy_gpu/trackpy-master/trackpy/gpu.py)
  - `bandpass` の `cupyx.scipy.ndimage` 呼び出しで `output=` を使わず、戻り値を再代入する形に維持。
  - `grey_dilation` に残っていたデバッグ `print` を削除。
  - `maxima` が 0 件のケースで、誤って「margin で全滅」と見える前に `Image contains no local maxima.` を返すチェックを復帰。
  - 未使用の `_cpu_grey_dilation_fallback` を削除。
- [`benchmarks/locate_3d_benchmark_lib.py`](/home/iwamoto/Desktop/iwa_project/trackpy_gpu/trackpy-master/benchmarks/locate_3d_benchmark_lib.py)
  - `ref_features > 0` かつ `target_features == 0` を `FAIL_EMPTY_DETECTION` として扱う実装を維持。
  - `Speedup Assessment` は `status != ok` を必ず `MISS` にする実装を維持。
- [`codex_report.md`](/home/iwamoto/Desktop/iwa_project/trackpy_gpu/trackpy-master/codex_report.md)
  - 実コードに存在しない CPU fallback 記述を削除。
  - `drop_close(precise=True)` が通常 locate 経路では優先度の低い仮説である点を明記。

## 今回の判断
- `cupy` が `0 features` のままでも speedup だけ `PASS` する状態は、benchmark 側で既に防げている。
- 一方で GPU 実装そのものについては、問題を隠すような CPU fallback は現時点では入れない。
- handoff 先が本質原因を追えるよう、GPU 側の失敗はそのまま見える状態を保つ。

## 現在のコード上の理解
- `bandpass` の CuPy インプレース更新問題は修正済み。
- `trackpy.feature.locate` は [`trackpy/feature.py`](/home/iwamoto/Desktop/iwa_project/trackpy_gpu/trackpy-master/trackpy/feature.py#L408) で `gpu_grey_dilation(..., precise=False)` を呼ぶ。
- したがって通常の 3D locate でまず疑うべき箇所は以下。
- `grey_dilation` の `threshold` 判定
- `cupyx.scipy.ndimage.grey_dilation` の挙動差
- margin 除外前後の候補数変化
- `refine_com_arr_3d` に渡る前の候補件数

## GPU agent 向けの確認順
1. `smoke3d` で `python / numba / cupy` を再実行し、`FAIL_EMPTY_DETECTION` にならず `target_features > 0` になるか確認。
2. `cupy` がまだ少数件しか出ない場合、`grey_dilation` の下記を CPU/GPU で並べて比較。
   - `threshold`
   - `cp.sum(maxima)` / `np.sum(maxima)`
   - margin 除外前件数
   - margin 除外後件数
3. `grey_dilation` が十分な件数を返しているのに最終結果が減る場合のみ、`refine_com_arr_3d` の入力件数と出力件数を追う。

## この時点での結論
- benchmark / report 側の誤判定は塞いだ。
- `bandpass` の明らかな不具合は修正済み。
- 残る本丸は `grey_dilation` 周辺の GPU/CPU 差分で、調査対象はかなり狭まっている。
