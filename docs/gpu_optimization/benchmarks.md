# GPU Benchmarks and Scaling Analysis

## Methodology
Benchmarks were conducted using synthetic 3D datasets with varying dimensions and feature densities. Each test compares the `numba` (CPU) engine against the `cupy` (GPU) engine.

- **Initialization**: "Cold" runs (first execution) include JIT compilation or kernel compilation time.
- **Measurement**: Steady-state performance is measured as the average of multiple "warm" runs.
- **Accuracy**: Measured by matching detected features against the CPU reference and calculating the Match Ratio and MARE (Mean Absolute Relative Error) for characterization.

## Environment
- **OS**: Linux (GPU-enabled environment)
- **GPU**: NVIDIA GPU
- **Drivers**: CUDA 11.x/12.x compatible
- **Python**: 3.12 (managed via `uv`)

## Scaling Trends
The CPU implementation (Numba) scales linearly with volume size, but the execution time grows rapidly for large 3D stacks. The GPU implementation exhibits significant sub-linear scaling for intermediate sizes due to high parallel occupancy.

### Large Dataset Breakdown (192x192x96)
- **CPU (Numba)**: ~515 ms
- **GPU (CuPy)**: ~102 ms
- **Speedup**: **5.05x**

The break-even point where GPU begins to consistently outperform CPU is approximately at the 64x64x32 volume size.
