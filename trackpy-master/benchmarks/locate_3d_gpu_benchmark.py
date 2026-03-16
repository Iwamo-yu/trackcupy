#!/usr/bin/env python
"""Generate runtime, accuracy, and report artifacts for 3D locate engines."""

import argparse

from locate_3d_benchmark_lib import (
    DEFAULT_ENGINES,
    SCENARIO_SETS,
    collect_environment_info,
    default_run_label,
    render_markdown_report,
    run_suite,
    write_outputs,
)


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark trackpy.locate on synthetic 3D workloads."
    )
    parser.add_argument("--engines", nargs="+", default=list(DEFAULT_ENGINES))
    parser.add_argument("--scenario-set", default="default3d")
    parser.add_argument("--cold-runs", type=int, default=1)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--tol", type=float, default=1.0)
    parser.add_argument("--output-dir", default="benchmarks/results")
    parser.add_argument("--run-label", default=None)
    args = parser.parse_args()

    if args.scenario_set not in SCENARIO_SETS:
        available = ", ".join(sorted(SCENARIO_SETS))
        raise SystemExit(
            f"Unknown scenario set '{args.scenario_set}'. Available: {available}"
        )

    run_label = args.run_label or default_run_label()
    scenarios = SCENARIO_SETS[args.scenario_set]
    runtime_df, accuracy_df = run_suite(
        scenarios=scenarios,
        engines=tuple(args.engines),
        ref_engine="python",
        tol=args.tol,
        cold_runs=args.cold_runs,
        warmup=args.warmup,
        repeats=args.repeats,
    )
    report_text = render_markdown_report(
        run_label=run_label,
        scenario_set=args.scenario_set,
        scenarios=scenarios,
        runtime_df=runtime_df,
        accuracy_df=accuracy_df,
        env_info=collect_environment_info(),
    )
    runtime_path, accuracy_path, report_path = write_outputs(
        args.output_dir, run_label, runtime_df, accuracy_df, report_text
    )

    print(runtime_df.to_string(index=False))
    print()
    print(accuracy_df.to_string(index=False))
    print()
    print(f"runtime_csv={runtime_path}")
    print(f"accuracy_csv={accuracy_path}")
    print(f"report_md={report_path}")


if __name__ == "__main__":
    main()
