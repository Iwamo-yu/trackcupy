"""Shared helpers for local 3D locate runtime and accuracy benchmarks."""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import tempfile
import textwrap
import time
from dataclasses import dataclass
from datetime import datetime
from importlib import import_module
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import trackpy as tp
from trackpy.artificial import draw_spots, gen_nonoverlapping_locations


DEFAULT_ENGINES = ("python", "numba", "cupy")
DEFAULT_SPEEDUP_GOAL = 1.5
STATUS_OK = "ok"
STATUS_FAIL_EMPTY_DETECTION = "FAIL_EMPTY_DETECTION"
RUNTIME_COLUMNS = [
    "scenario",
    "shape",
    "count",
    "diameter",
    "noise_level",
    "seed",
    "engine",
    "status",
    "cold_ms",
    "steady_mean_ms",
    "steady_min_ms",
    "steady_max_ms",
    "steady_std_ms",
    "features",
    "speedup_vs_python",
    "speedup_vs_numba",
]
ACCURACY_COLUMNS = [
    "scenario",
    "ref_engine",
    "engine",
    "status",
    "ref_features",
    "target_features",
    "matched",
    "match_ratio_ref",
    "rmse_xyz",
    "mae_z",
    "mae_y",
    "mae_x",
    "mass_mare",
    "signal_mare",
    "raw_mass_mare",
    "size_mare",
    "size_z_mare",
    "size_y_mare",
    "size_x_mare",
]


@dataclass(frozen=True)
class Scenario:
    name: str
    shape: tuple[int, int, int]
    count: int
    diameter: tuple[int, int, int]
    noise_level: int
    seed: int


SCENARIO_SETS = {
    "default3d": (
        Scenario("iso_baseline", (128, 128, 64), 200, (9, 9, 9), 20, 42),
        Scenario("iso_dense", (128, 128, 64), 500, (9, 9, 9), 20, 43),
        Scenario("aniso_baseline", (128, 128, 64), 200, (7, 9, 9), 20, 44),
        Scenario("iso_large", (192, 192, 96), 500, (9, 9, 9), 20, 45),
    ),
    "smoke3d": (
        Scenario("smoke_iso", (48, 48, 24), 8, (7, 7, 7), 10, 123),
    ),
}


def make_image(shape, count, diameter, noise_level, seed):
    rng = np.random.default_rng(seed)
    radius = tuple(d // 2 for d in diameter)
    margin = tuple(r + 1 for r in radius)
    separation = tuple(d * 3 for d in diameter)
    positions = gen_nonoverlapping_locations(shape, count, separation, margin)
    positions = positions + rng.random(positions.shape) * 0.2
    size = [d / 2 for d in diameter]
    image = draw_spots(shape, positions, size, noise_level)
    return image.astype(np.uint16, copy=False)


def run_locate(image, diameter, engine):
    start = time.perf_counter()
    features = tp.locate(image, diameter, engine=engine)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    return elapsed_ms, features


def benchmark_runtime(image, diameter, engine, cold_runs=1, warmup=2, repeats=5):
    """Measure one engine on a single image.

    ``cold_ms`` is the mean first-run latency across ``cold_runs`` fresh Python
    processes. Steady-state timings are collected in-process after ``warmup``.
    """
    cold_ms = np.nan
    features = np.nan
    if cold_runs > 0:
        cold_timings = []
        cold_counts = []
        for _ in range(cold_runs):
            elapsed_ms, feature_count = _run_locate_in_subprocess(
                image, diameter, engine
            )
            cold_timings.append(elapsed_ms)
            cold_counts.append(feature_count)
        cold_ms = float(np.mean(cold_timings))
        features = int(round(float(np.mean(cold_counts))))

    for _ in range(warmup):
        run_locate(image, diameter, engine)

    steady_timings = []
    steady_counts = []
    for _ in range(repeats):
        elapsed_ms, frame = run_locate(image, diameter, engine)
        steady_timings.append(elapsed_ms)
        steady_counts.append(len(frame))

    if steady_counts:
        features = int(round(float(np.mean(steady_counts))))

    if not steady_timings:
        raise ValueError("repeats must be at least 1")

    return {
        "engine": engine,
        "status": STATUS_OK,
        "cold_ms": cold_ms,
        "steady_mean_ms": float(np.mean(steady_timings)),
        "steady_min_ms": float(np.min(steady_timings)),
        "steady_max_ms": float(np.max(steady_timings)),
        "steady_std_ms": float(np.std(steady_timings)),
        "features": features,
    }


def compare_detection(image, diameter, engines, ref_engine="python", tol=1.0):
    detections = {}
    statuses = {}
    for engine in engines:
        try:
            _, detections[engine] = run_locate(image, diameter, engine)
            statuses[engine] = STATUS_OK
        except Exception as exc:
            detections[engine] = None
            statuses[engine] = _format_error(exc)

    ref_df = detections.get(ref_engine)
    ref_features = len(ref_df) if ref_df is not None else np.nan
    rows = []
    for engine in engines:
        target_df = detections[engine]
        target_features = len(target_df) if target_df is not None else np.nan
        status = statuses[engine]
        if (
            status == STATUS_OK
            and np.isfinite(ref_features)
            and ref_features > 0
            and np.isfinite(target_features)
            and target_features == 0
        ):
            status = STATUS_FAIL_EMPTY_DETECTION
        row = {
            "ref_engine": ref_engine,
            "engine": engine,
            "status": status,
            "ref_features": ref_features,
            "target_features": target_features,
        }
        if ref_df is not None and status == STATUS_OK:
            row.update(compare_characterization(ref_df, target_df, tol=tol))
        else:
            row.update(_empty_accuracy_metrics())
        rows.append(row)
    return pd.DataFrame(rows, columns=[c for c in ACCURACY_COLUMNS if c != "scenario"])


def compare_characterization(ref_df, tgt_df, tol=1.0):
    ref_xyz = _extract_xyz(ref_df)
    tgt_xyz = _extract_xyz(tgt_df)
    match = _match_positions(ref_xyz, tgt_xyz, tol=tol)
    result = {
        "matched": match["matched"],
        "match_ratio_ref": match["match_ratio_ref"],
        "rmse_xyz": match["rmse_xyz"],
        "mae_z": match["mae_z"],
        "mae_y": match["mae_y"],
        "mae_x": match["mae_x"],
        "mass_mare": np.nan,
        "signal_mare": np.nan,
        "raw_mass_mare": np.nan,
        "size_mare": np.nan,
        "size_z_mare": np.nan,
        "size_y_mare": np.nan,
        "size_x_mare": np.nan,
    }
    if match["matched"] == 0:
        return result

    ref_matched = ref_df.iloc[match["ref_indices"]].reset_index(drop=True)
    tgt_matched = tgt_df.iloc[match["tgt_indices"]].reset_index(drop=True)

    for col, key in (
        ("mass", "mass_mare"),
        ("signal", "signal_mare"),
        ("raw_mass", "raw_mass_mare"),
    ):
        result[key] = _mean_abs_relative_error(ref_matched[col], tgt_matched[col])

    ref_size_cols = [col for col in ("size_z", "size_y", "size_x") if col in ref_matched]
    tgt_size_cols = [col for col in ("size_z", "size_y", "size_x") if col in tgt_matched]
    if "size" in ref_matched and "size" in tgt_matched:
        result["size_mare"] = _mean_abs_relative_error(
            ref_matched["size"], tgt_matched["size"]
        )
    elif ref_size_cols and ref_size_cols == tgt_size_cols:
        key_map = {
            "size_z": "size_z_mare",
            "size_y": "size_y_mare",
            "size_x": "size_x_mare",
        }
        for col in ref_size_cols:
            result[key_map[col]] = _mean_abs_relative_error(
                ref_matched[col], tgt_matched[col]
            )
    return result


def run_suite(
    scenarios,
    engines,
    ref_engine="python",
    tol=1.0,
    cold_runs=1,
    warmup=2,
    repeats=5,
):
    runtime_rows = []
    accuracy_rows = []
    for scenario in scenarios:
        image = make_image(
            scenario.shape,
            scenario.count,
            scenario.diameter,
            scenario.noise_level,
            scenario.seed,
        )
        scenario_runtime_rows = []
        for engine in engines:
            base = _scenario_metadata(scenario)
            base["engine"] = engine
            try:
                row = benchmark_runtime(
                    image,
                    scenario.diameter,
                    engine,
                    cold_runs=cold_runs,
                    warmup=warmup,
                    repeats=repeats,
                )
            except Exception as exc:
                row = {
                    "engine": engine,
                    "status": _format_error(exc),
                    "cold_ms": np.nan,
                    "steady_mean_ms": np.nan,
                    "steady_min_ms": np.nan,
                    "steady_max_ms": np.nan,
                    "steady_std_ms": np.nan,
                    "features": np.nan,
                }
            scenario_runtime_rows.append({**base, **row})
        _add_speedups(scenario_runtime_rows)
        runtime_rows.extend(scenario_runtime_rows)

        accuracy_df = compare_detection(
            image,
            scenario.diameter,
            engines,
            ref_engine=ref_engine,
            tol=tol,
        )
        _merge_accuracy_status_into_runtime_rows(
            scenario_runtime_rows, accuracy_df.to_dict(orient="records")
        )
        for row in accuracy_df.to_dict(orient="records"):
            accuracy_rows.append({"scenario": scenario.name, **row})

    runtime_df = pd.DataFrame(runtime_rows, columns=RUNTIME_COLUMNS)
    accuracy_df = pd.DataFrame(accuracy_rows, columns=ACCURACY_COLUMNS)
    return runtime_df, accuracy_df


def collect_environment_info():
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "python_executable": sys.executable,
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "trackpy_version": getattr(tp, "__version__", "unknown"),
        "numpy_version": _module_version("numpy"),
        "pandas_version": _module_version("pandas"),
        "scipy_version": _module_version("scipy"),
        "numba_version": _module_version("numba"),
        "cupy_version": _module_version("cupy"),
        "nvidia_smi": _run_nvidia_smi(),
    }


def ensure_output_dir(path):
    output_dir = Path(path)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def default_run_label():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def write_outputs(output_dir, run_label, runtime_df, accuracy_df, report_text):
    output_dir = ensure_output_dir(output_dir)
    runtime_path = output_dir / f"runtime_{run_label}.csv"
    accuracy_path = output_dir / f"accuracy_{run_label}.csv"
    report_path = output_dir / f"report_{run_label}.md"
    runtime_df.to_csv(runtime_path, index=False)
    accuracy_df.to_csv(accuracy_path, index=False)
    report_path.write_text(report_text, encoding="utf-8")
    return runtime_path, accuracy_path, report_path


def render_markdown_report(
    run_label,
    scenario_set,
    scenarios,
    runtime_df,
    accuracy_df,
    env_info,
    speedup_goal=DEFAULT_SPEEDUP_GOAL,
):
    lines = [
        f"# 3D Locate GPU Benchmark Report: {run_label}",
        "",
        "## Environment",
        "",
    ]
    for key in (
        "timestamp",
        "python_executable",
        "python_version",
        "platform",
        "trackpy_version",
        "numpy_version",
        "pandas_version",
        "scipy_version",
        "numba_version",
        "cupy_version",
        "nvidia_smi",
    ):
        lines.append(f"- {key}: {env_info.get(key, 'unknown')}")

    lines.extend(
        [
            "",
            "## Scenario Set",
            "",
            f"- name: `{scenario_set}`",
            f"- engines: `{', '.join(runtime_df['engine'].dropna().unique())}`",
            f"- speedup goal: `cupy >= {speedup_goal:.1f}x numba`",
            "",
            "| scenario | shape | count | diameter | noise_level | seed |",
            "| --- | --- | ---: | --- | ---: | ---: |",
        ]
    )
    for scenario in scenarios:
        lines.append(
            f"| {scenario.name} | {scenario.shape} | {scenario.count} | "
            f"{scenario.diameter} | {scenario.noise_level} | {scenario.seed} |"
        )

    lines.extend(
        [
            "",
            "## Runtime",
            "",
            _dataframe_to_markdown(runtime_df, RUNTIME_COLUMNS),
            "",
            "## Accuracy",
            "",
            _dataframe_to_markdown(accuracy_df, ACCURACY_COLUMNS),
            "",
            "## Speedup Assessment",
            "",
        ]
    )
    for scenario in scenarios:
        subset = runtime_df[runtime_df["scenario"] == scenario.name]
        cupy_row = subset[subset["engine"] == "cupy"]
        if cupy_row.empty:
            lines.append(f"- {scenario.name}: MISS (cupy row missing)")
            continue
        speedup = cupy_row["speedup_vs_numba"].iloc[0]
        status = cupy_row["status"].iloc[0]
        accuracy_subset = accuracy_df[
            (accuracy_df["scenario"] == scenario.name) & (accuracy_df["engine"] == "cupy")
        ]
        if not accuracy_subset.empty and status == STATUS_OK:
            status = accuracy_subset["status"].iloc[0]
        if status != STATUS_OK:
            lines.append(f"- {scenario.name}: MISS ({status})")
            continue
        if not np.isfinite(speedup):
            lines.append(f"- {scenario.name}: MISS ({status})")
            continue
        verdict = "PASS" if speedup >= speedup_goal else "MISS"
        lines.append(
            f"- {scenario.name}: {verdict} "
            f"(speedup_vs_numba={speedup:.3f}, status={status})"
        )
    return "\n".join(lines) + "\n"


def _run_locate_in_subprocess(image, diameter, engine):
    code = textwrap.dedent(
        """
        import json
        import sys
        import time
        import numpy as np
        import trackpy as tp

        image = np.load(sys.argv[1])
        diameter = tuple(json.loads(sys.argv[2]))
        engine = sys.argv[3]
        start = time.perf_counter()
        features = tp.locate(image, diameter, engine=engine)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        print(json.dumps({"elapsed_ms": elapsed_ms, "features": int(len(features))}))
        """
    ).strip()
    fd, image_path = tempfile.mkstemp(suffix=".npy")
    os.close(fd)
    try:
        np.save(image_path, image)
        completed = subprocess.run(
            [sys.executable, "-c", code, image_path, json.dumps(list(diameter)), engine],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            error_text = (completed.stderr or completed.stdout).strip()
            raise RuntimeError(error_text or f"Subprocess failed for {engine}")
        payload = json.loads(completed.stdout.strip().splitlines()[-1])
        return float(payload["elapsed_ms"]), int(payload["features"])
    finally:
        try:
            os.unlink(image_path)
        except OSError:
            pass


def _scenario_metadata(scenario):
    return {
        "scenario": scenario.name,
        "shape": str(tuple(scenario.shape)),
        "count": scenario.count,
        "diameter": str(tuple(scenario.diameter)),
        "noise_level": scenario.noise_level,
        "seed": scenario.seed,
    }


def _add_speedups(rows):
    baselines = {
        row["engine"]: row["steady_mean_ms"]
        for row in rows
        if np.isfinite(row["steady_mean_ms"])
    }
    base_python = baselines.get("python", np.nan)
    base_numba = baselines.get("numba", np.nan)
    for row in rows:
        value = row["steady_mean_ms"]
        row["speedup_vs_python"] = (
            float(base_python / value)
            if np.isfinite(base_python) and np.isfinite(value)
            else np.nan
        )
        row["speedup_vs_numba"] = (
            float(base_numba / value)
            if np.isfinite(base_numba) and np.isfinite(value)
            else np.nan
        )


def _merge_accuracy_status_into_runtime_rows(runtime_rows, accuracy_rows):
    accuracy_by_engine = {row["engine"]: row for row in accuracy_rows}
    for runtime_row in runtime_rows:
        accuracy_row = accuracy_by_engine.get(runtime_row["engine"])
        if accuracy_row is None:
            continue
        accuracy_status = accuracy_row.get("status")
        if accuracy_status and accuracy_status != STATUS_OK:
            runtime_row["status"] = accuracy_status


def _extract_xyz(df):
    if df is None or len(df) == 0:
        return np.empty((0, 3), dtype=float)
    return df[["z", "y", "x"]].to_numpy(dtype=float)


def _match_positions(ref_xyz, tgt_xyz, tol):
    if len(ref_xyz) == 0 or len(tgt_xyz) == 0:
        return {
            "matched": 0,
            "match_ratio_ref": 0.0,
            "rmse_xyz": np.nan,
            "mae_z": np.nan,
            "mae_y": np.nan,
            "mae_x": np.nan,
            "ref_indices": np.array([], dtype=int),
            "tgt_indices": np.array([], dtype=int),
        }

    tree = cKDTree(tgt_xyz)
    dist, idx = tree.query(ref_xyz, k=1)
    mask = np.isfinite(dist) & (dist <= tol)
    ref_indices = np.flatnonzero(mask)
    tgt_indices = idx[mask].astype(int, copy=False)
    matched = int(mask.sum())
    if matched == 0:
        return {
            "matched": 0,
            "match_ratio_ref": 0.0,
            "rmse_xyz": np.nan,
            "mae_z": np.nan,
            "mae_y": np.nan,
            "mae_x": np.nan,
            "ref_indices": ref_indices,
            "tgt_indices": tgt_indices,
        }
    delta = ref_xyz[ref_indices] - tgt_xyz[tgt_indices]
    mae = np.mean(np.abs(delta), axis=0)
    rmse = float(np.sqrt(np.mean(np.sum(delta ** 2, axis=1))))
    return {
        "matched": matched,
        "match_ratio_ref": matched / max(len(ref_xyz), 1),
        "rmse_xyz": rmse,
        "mae_z": float(mae[0]),
        "mae_y": float(mae[1]),
        "mae_x": float(mae[2]),
        "ref_indices": ref_indices,
        "tgt_indices": tgt_indices,
    }


def _mean_abs_relative_error(ref_values, tgt_values, epsilon=1e-12):
    ref = np.asarray(ref_values, dtype=float)
    tgt = np.asarray(tgt_values, dtype=float)
    denom = np.maximum(np.abs(ref), epsilon)
    return float(np.mean(np.abs(ref - tgt) / denom))


def _empty_accuracy_metrics():
    return {
        "matched": np.nan,
        "match_ratio_ref": np.nan,
        "rmse_xyz": np.nan,
        "mae_z": np.nan,
        "mae_y": np.nan,
        "mae_x": np.nan,
        "mass_mare": np.nan,
        "signal_mare": np.nan,
        "raw_mass_mare": np.nan,
        "size_mare": np.nan,
        "size_z_mare": np.nan,
        "size_y_mare": np.nan,
        "size_x_mare": np.nan,
    }


def _module_version(name):
    try:
        module = import_module(name)
    except Exception as exc:
        return _format_error(exc)
    return getattr(module, "__version__", "unknown")


def _run_nvidia_smi():
    try:
        completed = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,driver_version",
                "--format=csv,noheader",
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return _format_error(exc)
    if completed.returncode != 0:
        error_text = (completed.stderr or completed.stdout).strip()
        return error_text or f"nvidia-smi exited with {completed.returncode}"
    return "; ".join(line.strip() for line in completed.stdout.splitlines() if line.strip())


def _dataframe_to_markdown(df, columns):
    subset = df.copy()
    for column in columns:
        if column not in subset:
            subset[column] = np.nan
    subset = subset[columns]
    if subset.empty:
        return "_No rows_"
    return subset.to_markdown(index=False)


def _format_error(exc):
    return f"ERROR: {type(exc).__name__}: {exc}"
