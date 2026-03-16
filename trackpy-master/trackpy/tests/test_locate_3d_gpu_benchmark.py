import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
BENCHMARKS_DIR = REPO_ROOT / "benchmarks"
if str(BENCHMARKS_DIR) not in sys.path:
    sys.path.insert(0, str(BENCHMARKS_DIR))

import locate_3d_benchmark_lib as benchlib


def test_compare_characterization_identical_frames():
    frame = pd.DataFrame(
        {
            "z": [1.0, 2.0],
            "y": [3.0, 4.0],
            "x": [5.0, 6.0],
            "mass": [10.0, 11.0],
            "signal": [4.0, 5.0],
            "raw_mass": [12.0, 13.0],
            "size": [2.0, 2.5],
        }
    )

    result = benchlib.compare_characterization(frame, frame, tol=0.1)

    assert result["matched"] == 2
    assert result["match_ratio_ref"] == 1.0
    assert result["rmse_xyz"] == 0.0
    assert result["mass_mare"] == 0.0
    assert result["signal_mare"] == 0.0
    assert result["raw_mass_mare"] == 0.0
    assert result["size_mare"] == 0.0


def test_run_suite_marks_missing_cupy_with_error():
    runtime_df, accuracy_df = benchlib.run_suite(
        scenarios=benchlib.SCENARIO_SETS["smoke3d"],
        engines=("python", "cupy"),
        cold_runs=0,
        warmup=0,
        repeats=1,
    )

    assert list(runtime_df["engine"]) == ["python", "cupy"]
    assert runtime_df.loc[runtime_df["engine"] == "python", "status"].iloc[0] == "ok"
    cupy_runtime = runtime_df.loc[runtime_df["engine"] == "cupy"].iloc[0]
    assert cupy_runtime["status"].startswith("ERROR:")
    cupy_accuracy = accuracy_df.loc[accuracy_df["engine"] == "cupy"].iloc[0]
    assert cupy_accuracy["status"].startswith("ERROR:")
    assert np.isnan(cupy_accuracy["rmse_xyz"])


def test_compare_detection_marks_empty_detection_failure(monkeypatch):
    image = benchlib.make_image((48, 48, 24), 8, (7, 7, 7), 10, 123)
    python_locate = benchlib.run_locate

    def fake_run_locate(img, diameter, engine):
        if engine == "cupy":
            return 1.0, pd.DataFrame(columns=["z", "y", "x", "mass", "size", "ecc", "signal", "raw_mass"])
        return python_locate(img, diameter, engine)

    monkeypatch.setattr(benchlib, "run_locate", fake_run_locate)
    accuracy_df = benchlib.compare_detection(
        image,
        (7, 7, 7),
        ("python", "cupy"),
        ref_engine="python",
        tol=1.0,
    )

    cupy_row = accuracy_df.loc[accuracy_df["engine"] == "cupy"].iloc[0]
    assert cupy_row["status"] == benchlib.STATUS_FAIL_EMPTY_DETECTION
    assert cupy_row["target_features"] == 0
    assert np.isnan(cupy_row["rmse_xyz"])


def test_report_marks_empty_detection_as_miss():
    runtime_df = pd.DataFrame(
        [
            {
                "scenario": "smoke_iso",
                "shape": "(48, 48, 24)",
                "count": 8,
                "diameter": "(7, 7, 7)",
                "noise_level": 10,
                "seed": 123,
                "engine": "python",
                "status": benchlib.STATUS_OK,
                "cold_ms": np.nan,
                "steady_mean_ms": 10.0,
                "steady_min_ms": 10.0,
                "steady_max_ms": 10.0,
                "steady_std_ms": 0.0,
                "features": 23,
                "speedup_vs_python": 1.0,
                "speedup_vs_numba": np.nan,
            },
            {
                "scenario": "smoke_iso",
                "shape": "(48, 48, 24)",
                "count": 8,
                "diameter": "(7, 7, 7)",
                "noise_level": 10,
                "seed": 123,
                "engine": "cupy",
                "status": benchlib.STATUS_FAIL_EMPTY_DETECTION,
                "cold_ms": np.nan,
                "steady_mean_ms": 1.0,
                "steady_min_ms": 1.0,
                "steady_max_ms": 1.0,
                "steady_std_ms": 0.0,
                "features": 0,
                "speedup_vs_python": 10.0,
                "speedup_vs_numba": 10.0,
            },
        ],
        columns=benchlib.RUNTIME_COLUMNS,
    )
    accuracy_df = pd.DataFrame(
        [
            {
                "scenario": "smoke_iso",
                "ref_engine": "python",
                "engine": "python",
                "status": benchlib.STATUS_OK,
                "ref_features": 23,
                "target_features": 23,
                "matched": 23,
                "match_ratio_ref": 1.0,
                "rmse_xyz": 0.0,
                "mae_z": 0.0,
                "mae_y": 0.0,
                "mae_x": 0.0,
                "mass_mare": 0.0,
                "signal_mare": 0.0,
                "raw_mass_mare": 0.0,
                "size_mare": 0.0,
                "size_z_mare": np.nan,
                "size_y_mare": np.nan,
                "size_x_mare": np.nan,
            },
            {
                "scenario": "smoke_iso",
                "ref_engine": "python",
                "engine": "cupy",
                "status": benchlib.STATUS_FAIL_EMPTY_DETECTION,
                "ref_features": 23,
                "target_features": 0,
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
            },
        ],
        columns=benchlib.ACCURACY_COLUMNS,
    )

    report = benchlib.render_markdown_report(
        run_label="unit",
        scenario_set="smoke3d",
        scenarios=benchlib.SCENARIO_SETS["smoke3d"],
        runtime_df=runtime_df,
        accuracy_df=accuracy_df,
        env_info={},
    )

    assert "MISS (FAIL_EMPTY_DETECTION)" in report


def test_cli_writes_all_artifacts(tmp_path):
    run_label = "pytest_smoke"
    output_dir = tmp_path / "results"
    completed = subprocess.run(
        [
            sys.executable,
            "benchmarks/locate_3d_gpu_benchmark.py",
            "--scenario-set",
            "smoke3d",
            "--engines",
            "python",
            "cupy",
            "--cold-runs",
            "0",
            "--warmup",
            "0",
            "--repeats",
            "1",
            "--output-dir",
            str(output_dir),
            "--run-label",
            run_label,
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    runtime_path = output_dir / f"runtime_{run_label}.csv"
    accuracy_path = output_dir / f"accuracy_{run_label}.csv"
    report_path = output_dir / f"report_{run_label}.md"
    assert runtime_path.exists()
    assert accuracy_path.exists()
    assert report_path.exists()

    runtime_df = pd.read_csv(runtime_path)
    accuracy_df = pd.read_csv(accuracy_path)
    report_text = report_path.read_text(encoding="utf-8")
    assert {"scenario", "engine", "status", "steady_mean_ms"}.issubset(runtime_df.columns)
    assert {"scenario", "engine", "status", "rmse_xyz"}.issubset(accuracy_df.columns)
    assert "Speedup Assessment" in report_text
