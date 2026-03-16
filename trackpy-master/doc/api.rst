.. _api_ref:

API reference
=============
The core functionality of trackcupy is grouped into three separate steps:

1. Locating features in an image
2. Refining feature coordinates to obtain subpixel precision
3. Identifying features through time, linking them into trajectories.

Convenience functions for feature finding, refinement, and linking are readily available:

.. autosummary::
    :toctree: generated/

    trackcupy.locate
    trackcupy.batch
    trackcupy.link

For more control on your tracking "pipeline", the following core functions are provided:


Feature finding
---------------
.. autosummary::
    :toctree: generated/

    trackcupy.grey_dilation
    trackcupy.find_link


Coordinate refinement
---------------------
.. autosummary::
    :toctree: generated/

    trackcupy.refine_com
    trackcupy.refine_leastsq

Linking
-------
.. autosummary::
    :toctree: generated/

    trackcupy.link
    trackcupy.link_iter
    trackcupy.link_df_iter
    trackcupy.link_partial
    trackcupy.reconnect_traj_patch


:func:`~trackcupy.linking.link` and :func:`~trackcupy.linking.link_df_iter` run
the same underlying code. :func:`~trackcupy.linking.link` operates on a single
DataFrame containing data for an entire movie.
:func:`~trackcupy.linking.link_df_iter` streams through larger data sets,
in the form of one DataFrame for each video frame.
:func:`~trackcupy.linking.link_iter` streams through a series of numpy
ndarrays.
:func:`~trackcupy.linking.link_partial` can patch a region of trajectories in
an already linked dataset.


See the tutorial on large data sets for more.

Static Analysis
---------------

.. autosummary::
    :toctree: generated/

    trackcupy.static.proximity
    trackcupy.static.pair_correlation_2d
    trackcupy.static.pair_correlation_3d
    trackcupy.static.cluster

Motion Analysis
---------------

.. autosummary::
    :toctree: generated/

    trackcupy.motion.msd
    trackcupy.motion.imsd
    trackcupy.motion.emsd
    trackcupy.motion.compute_drift
    trackcupy.motion.subtract_drift
    trackcupy.motion.vanhove
    trackcupy.motion.relate_frames
    trackcupy.motion.velocity_corr
    trackcupy.motion.direction_corr
    trackcupy.motion.is_typical
    trackcupy.motion.diagonal_size
    trackcupy.motion.theta_entropy
    trackcupy.motion.min_rolling_theta_entropy
    trackcupy.filtering.filter_stubs
    trackcupy.filtering.filter_clusters

Prediction Framework
--------------------

Trackpy extends the Crocker--Grier algoritm using a prediction framework, described in the prediction tutorial.

.. autosummary::
   :toctree: generated/

   trackcupy.predict.NullPredict     
   trackcupy.predict.ChannelPredict
   trackcupy.predict.DriftPredict
   trackcupy.predict.NearestVelocityPredict
   trackcupy.predict.predictor
   trackcupy.predict.instrumented

Plotting Tools
--------------

Trackpy includes functions for plotting the data in ways that are commonly useful. If you don't find what you need here, you can plot the data any way you like using matplotlib, seaborn, or any other plotting library.

.. autosummary::
    :toctree: generated/

    trackcupy.annotate
    trackcupy.scatter
    trackcupy.plot_traj
    trackcupy.annotate3d
    trackcupy.scatter3d
    trackcupy.plot_traj3d
    trackcupy.plot_displacements
    trackcupy.subpx_bias
    trackcupy.plot_density_profile

These two are almost too simple to justify their existence -- just a convenient shorthand for a common plotting task.

.. autosummary::
    :toctree: generated/

    trackcupy.mass_ecc
    trackcupy.mass_size

Image Conversion
----------------

By default, :func:`~trackcupy.feature.locate` applies a bandpass and a percentile-based
threshold to the image(s) before finding features. You can turn off this functionality
using ``preprocess=False, percentile=0``.) In many cases, the default bandpass, which
guesses good length scales from the ``diameter`` parameter, "just works." But if you want
to executre these steps manually, you can.

.. autosummary::
    :toctree: generated/

    trackcupy.find.percentile_threshold
    trackcupy.preprocessing.bandpass
    trackcupy.preprocessing.lowpass
    trackcupy.preprocessing.scale_to_gamut
    trackcupy.preprocessing.invert_image
    trackcupy.preprocessing.convert_to_int

Framewise Data Storage & Retrieval Interface
--------------------------------------------

Trackpy implements a generic interface that could be used to store and
retrieve particle tracking data in any file format. We hope that it can
make it easier for researchers who use different file formats to exchange data. Any in-house format could be accessed using the same simple interface in trackcupy.

At present, the interface is implemented only for HDF5 files. There are
several different implementations, each with different performance
optimizations. :class:`~trackcupy.framewise_data.PandasHDFStoreBig` is a good general-purpose choice.

.. autosummary::
    :toctree: generated/

    trackcupy.PandasHDFStore
    trackcupy.PandasHDFStoreBig
    trackcupy.PandasHDFStoreSingleNode
    trackcupy.FramewiseData

That last class cannot be used directly; it is meant to be subclassed
to support other formats. See *Writing Your Own Interface* in the streaming tutorial for
more.

Logging
-------

Trackpy issues log messages. This functionality is mainly used to report the
progress of lengthy jobs, but it may be used in the future to report details of
feature-finding and linking for debugging purposes.

When trackcupy is imported, it automatically calls `handle_logging()`, which sets
the logging level and attaches a logging handler that plays nicely with
IPython notebooks. You can override this by calling `ignore_logging()` and
configuring the logger however you like.

.. autosummary::
    :toctree: generated/

    trackcupy.quiet
    trackcupy.handle_logging
    trackcupy.ignore_logging

Utility functions
-----------------

.. autosummary::
    :toctree: generated/

    trackcupy.minmass_v03_change
    trackcupy.minmass_v04_change
    trackcupy.utils.fit_powerlaw

Diagnostic functions
--------------------

.. autosummary::
   :toctree: generated/

   trackcupy.diag.performance_report
   trackcupy.diag.dependencies

Low-Level API (Advanced)
------------------------

Switching Between Numba and Pure Python
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Trackpy implements the most intensive (read: slowest) parts of the core feature-finding and linking algorithm in pure Python (with numpy) and also in `numba <http://numba.pydata.org/>`_, which accelerates Python code. Numba can offer a major performance boost, but it is still relatively new, and it can be challenging to use. If numba is available, trackcupy will use the numba implementation by default; otherwise, it will use pure Python. The following functions allow sophisticated users to manually switch between numba and pure-Python modes. This may be used, for example, to measure the performance of these two implementations on your data.

.. autosummary::
   :toctree: generated/

   trackcupy.enable_numba
   trackcupy.disable_numba


Experimental CuPy Engine for 3D Locate
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``trackcupy.locate`` and ``trackcupy.refine_com`` accept ``engine='cupy'`` as an
experimental option for GPU-accelerated 3D workflows. This requires CuPy and
a CUDA-compatible NVIDIA environment. The default ``engine='auto'`` behavior
is unchanged.

Typical usage:

.. code-block:: python

   import trackcupy as tp
   f = tp.locate(image_3d, diameter=(9, 9, 9), engine='cupy')


Low-Level Linking API
^^^^^^^^^^^^^^^^^^^^^

All of the linking functions in trackcupy provide the same level of control over the linking algorithm itself. For almost all users, the functions above will be sufficient. But :func:`~trackcupy.linking.link_df` and :func:`~trackcupy.linking.link_df_iter` above do assume that the data is stored in a pandas DataFrame. For users who want to use some other iterable data structure, the functions below provide direct access to the linking code.

.. autosummary::
    :toctree: generated/

    trackcupy.link_iter
    trackcupy.link

And the following classes can be subclassed to implement a customized linking procedure.

.. autosummary::
    :toctree: generated/

    trackcupy.SubnetOversizeException

Masks
^^^^^

These functions may also be useful for rolling your own algorithms:

.. autosummary::
    :toctree: generated/

    trackcupy.masks.binary_mask
    trackcupy.masks.r_squared_mask
    trackcupy.masks.x_squared_masks
    trackcupy.masks.cosmask
    trackcupy.masks.sinmask
    trackcupy.masks.theta_mask
    trackcupy.masks.gaussian_kernel
    trackcupy.masks.mask_image
    trackcupy.masks.slice_image

Full API reference
------------------

A full overview of all modules and functions can be found below:

.. autosummary::
    :toctree: generated/
    :recursive:

    trackcupy

..
  Note: we excluded trackcupy.tests in conf.py (autosummary_mock_imports)
