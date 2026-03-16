# Development Log: GPU Optimization Journey

## Phase 1: Accuracy Restoration (Cycle 1)
**Goal**: Solve the issue where CuPy detected 0 features in 3D smoke tests.

- **Discovery**: The `bandpass` filter was using `float64` for background subtraction, whereas the CPU version used integer truncation. This caused significant pixel-level differences.
- **Solution**: Modified `gpu.py` to respect the input `dtype` for background boxcar filtering, aligning integer truncation behavior.
- **Outcome**: Accuracy improved from 0% to 100% on the `smoke3d` dataset.

## Phase 2: Refine Path Parallelization (Cycle 2)
**Goal**: Reach >2x speedup vs. Numba.

- **Discovery**: The original `refine_com_arr_3d` used a Python loop over features, calling `.item()` on CuPy objects. Each `.item()` call triggered a host-device synchronization, becoming the primary bottleneck.
- **Solution**: Implemented a custom CUDA `RawKernel` that processes all features in parallel.
- **Architecture**:
    - Each CUDA block is assigned one feature.
    - Warp-level shuffle primitives (`__shfl_down_sync`) are used for parallel reduction of mass and centroids.
    - Shared memory is used to store intermediate results, avoiding global memory latency.
- **Outcome**: Achieved a 5.1x speedup on large datasets.

## Phase 3: Device-Resident Flow
**Goal**: Further reduce overhead.

- **Action**: Optimized `trackcupy.feature.locate` to avoid unnecessary rescaling and NumPy conversions when `engine='cupy'` is selected.
- **Result**: The image data stays on the device from the moment it is loaded until the final refined coordinates are produced.
