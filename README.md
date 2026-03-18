trackcupy
=========

trackcupy is a high-performance, GPU-accelerated fork of [trackpy](https://github.com/soft-matter/trackpy).

What is it?
-----------

**trackcupy** is a particle-tracking toolkit optimized for GPU acceleration. It is based on the [trackpy](https://github.com/soft-matter/trackpy) project and extends it with CuPy-powered algorithms.

[**Read the original trackpy walkthrough**](http://soft-matter.github.io/trackpy/dev/tutorial/walkthrough.html) to skim or study an example project from start to finish.

GPU Acceleration
----------------

trackcupy includes a high-performance GPU engine powered by CuPy. It is specifically optimized for 3D particle detection, offering up to **5x speedup** on large volumetric datasets compared to Numba.

For more details, see the [GPU Optimization Documentation](docs/gpu_optimization/README.md).

Documentation
-------------

[**Read the trackpy documentation**](http://soft-matter.github.io/trackpy/) for:

- an introduction
- tutorials on the basics, 3D tracking, and much, much more
- easy [installation instructions](http://soft-matter.github.io/trackpy/dev/installation.html)
- the reference guide

If you use trackcupy for published research, please
[cite the release](http://soft-matter.github.io/trackpy/dev/introduction.html#citing-trackpy)
both to credit the contributors, and to direct your readers to the exact
version of trackpy/trackcupy they could use to reproduce your results.
