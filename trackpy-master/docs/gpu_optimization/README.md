# GPU Optimization for trackcupy

## Overview
This directory contains technical documentation and performance results for the 3D particle detection GPU implementation in `trackcupy`. The `cupy` engine has been optimized to provide high-performance tracking for large volumetric datasets.

## Key Features
- **Device-Resident Pipeline**: Data remains on the GPU throughout the entire `bandpass` -> `grey_dilation` -> `refine` process, minimizing costly host-device transfers.
- **CUDA RawKernels**: Custom C++ kernels were developed for 3D center-of-mass refinement, parallelizing the workload across all detected features simultaneously.
- **High Scalability**: The GPU speedup increases as the image size and feature count grow, making it ideal for large-scale experiments.

## Performance Summary
Benchmark results on an NVIDIA GPU vs. a JIT-optimized CPU (Numba):

| Dataset (3D) | Dimensions | Speedup (vs. Numba) | Accuracy (vs. CPU) |
| :--- | :--- | :---: | :---: |
| Small (smoke3d) | 48x48x24 | 1.2x | 95.7% |
| Medium (baseline) | 128x128x64 | 3.6x | 96.8% |
| **Large (iso_large)** | 192x192x96 | **5.1x** | 98.1% |

## Documentation
- [Benchmarks](benchmarks.md): Detailed methodology, environment, and scaling trends.
- [Development Log](development_log.md): Implementation history, challenges, and architectural decisions.
