#!/usr/bin/env python
"""Simple 3D locate benchmark for python/numba/cupy engines.

Example
-------
python benchmarks/locate_3d_gpu_benchmark.py --engines python numba cupy
"""

import argparse
import time

import numpy as np

import trackpy as tp
from trackpy.artificial import draw_spots, gen_nonoverlapping_locations


def make_image(shape, count, diameter, noise_level, seed):
    rng = np.random.default_rng(seed)
    radius = tuple([d // 2 for d in diameter])
    margin = tuple([r + 1 for r in radius])
    separation = tuple([d * 3 for d in diameter])
    positions = gen_nonoverlapping_locations(shape, count, separation, margin)
    positions = positions + rng.random(positions.shape) * 0.2
    size = [d / 2 for d in diameter]
    image = draw_spots(shape, positions, size, noise_level)
    return image.astype(np.uint16, copy=False)


def run_once(image, diameter, engine):
    start = time.perf_counter()
    features = tp.locate(image, diameter, engine=engine)
    elapsed = (time.perf_counter() - start) * 1000.0
    return elapsed, len(features)


def benchmark(image, diameter, engine, warmup, repeats):
    for _ in range(warmup):
        run_once(image, diameter, engine)
    timings = []
    counts = []
    for _ in range(repeats):
        elapsed, count = run_once(image, diameter, engine)
        timings.append(elapsed)
        counts.append(count)
    return {
        "engine": engine,
        "mean_ms": float(np.mean(timings)),
        "min_ms": float(np.min(timings)),
        "max_ms": float(np.max(timings)),
        "std_ms": float(np.std(timings)),
        "features": int(np.mean(counts)),
    }


def main():
    parser = argparse.ArgumentParser(description="Benchmark trackpy.locate on 3D data.")
    parser.add_argument("--shape", nargs=3, type=int, default=[128, 128, 64])
    parser.add_argument("--count", type=int, default=200)
    parser.add_argument("--diameter", nargs=3, type=int, default=[9, 9, 9])
    parser.add_argument("--noise-level", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--engines", nargs="+", default=["python", "numba", "cupy"])
    args = parser.parse_args()

    shape = tuple(args.shape)
    diameter = tuple(args.diameter)
    image = make_image(shape, args.count, diameter, args.noise_level, args.seed)

    print("shape,count,diameter,noise,warmup,repeats")
    print(f"{shape},{args.count},{diameter},{args.noise_level},{args.warmup},{args.repeats}")
    print("engine,mean_ms,min_ms,max_ms,std_ms,features")

    for engine in args.engines:
        try:
            result = benchmark(image, diameter, engine, args.warmup, args.repeats)
        except Exception as exc:
            print(f"{engine},ERROR,{type(exc).__name__},{exc}")
            continue
        print(
            "{engine},{mean_ms:.3f},{min_ms:.3f},{max_ms:.3f},{std_ms:.3f},{features}".format(
                **result
            )
        )


if __name__ == "__main__":
    main()
