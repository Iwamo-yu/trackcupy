import warnings
import logging
import numpy as np

logger = logging.getLogger(__name__)


def import_cupy():
    """Import cupy lazily.

    Returns
    -------
    module
        The imported `cupy` module.

    Raises
    ------
    ImportError
        If cupy is not installed.
    """
    try:
        import cupy as cp
    except ImportError as exc:
        raise ImportError(
            "The 'cupy' engine requires CuPy. Install cupy-cuda11x or "
            "cupy-cuda12x and a compatible NVIDIA CUDA driver."
        ) from exc
    return cp


def cupy_available():
    """Return True when CuPy is importable."""
    try:
        import_cupy()
    except ImportError:
        return False
    return True


def require_cupy(context="this operation"):
    """Raise a clear ImportError if CuPy is not available."""
    try:
        import_cupy()
    except ImportError as exc:
        raise ImportError(f"CuPy is required for {context}.") from exc


def asarray(array):
    """Convert input to a CuPy array."""
    cp = import_cupy()
    return cp.asarray(array)


def asnumpy(array):
    """Convert input to a NumPy array if it is a CuPy array."""
    if cupy_available():
        cp = import_cupy()
        if isinstance(array, cp.ndarray):
            return cp.asnumpy(array)
    return np.asarray(array)


def _import_cupyx_ndimage():
    try:
        from cupyx.scipy import ndimage
    except ImportError as exc:
        raise ImportError(
            "The 'cupy' engine requires cupyx.scipy.ndimage support."
        ) from exc
    return ndimage


def _validate_tuple(value, ndim):
    if not hasattr(value, "__iter__"):
        return (value,) * ndim
    if len(value) == ndim:
        return tuple(value)
    raise ValueError("List length should have same length as image dimensions.")


def _gaussian_kernel(sigma, truncate=4.0):
    lw = int(truncate * sigma + 0.5)
    x = np.arange(-lw, lw + 1)
    result = np.exp(x**2 / (-2 * sigma**2))
    return result / np.sum(result)


def _boxcar_nearest(arr, size):
    cp = import_cupy()
    ndimage = _import_cupyx_ndimage()

    size = _validate_tuple(size, arr.ndim)
    if not np.all([x & 1 for x in size]):
        raise ValueError("Smoothing size must be an odd integer. Round up.")

    # CPU trackcupy.preprocessing.boxcar maintains the input dtype,
    # which leads to integer truncation for integer images.
    # We must match this behavior to preserve accuracy.
    src = cp.array(arr, copy=True)
    dst = cp.empty_like(src)

    for axis, width in enumerate(size):
        if width > 1:
            ndimage.uniform_filter1d(
                src, width, axis=axis,
                output=dst,
                mode='nearest',
                cval=0.0,
            )
            src, dst = dst, src
    return src


def _lowpass(arr, sigma, truncate, dtype=None):
    cp = import_cupy()
    ndimage = _import_cupyx_ndimage()

    if dtype is None:
        dtype = cp.float64

    sigma = _validate_tuple(sigma, arr.ndim)
    src = cp.array(arr, dtype=dtype, copy=True)
    dst = cp.empty_like(src)

    for axis, s in enumerate(sigma):
        if s > 0:
            kernel = cp.asarray(_gaussian_kernel(s, truncate), dtype=dtype)
            ndimage.correlate1d(
                src, kernel, axis=axis,
                output=dst,
                mode='constant',
                cval=0.0,
            )
            src, dst = dst, src
    return src


def bandpass(image, lshort, llong, threshold=None, truncate=4):
    """GPU variant of preprocessing.bandpass that returns a NumPy array."""
    return asnumpy(gpu_bandpass(image, lshort, llong, threshold, truncate))


def gpu_bandpass(image, lshort, llong, threshold=None, truncate=4):
    """GPU variant of preprocessing.bandpass that returns a CuPy array."""
    cp = import_cupy()

    arr = cp.asarray(image)
    lshort = _validate_tuple(lshort, arr.ndim)
    llong = _validate_tuple(llong, arr.ndim)

    if np.any([x >= y for (x, y) in zip(lshort, llong)]):
        raise ValueError("The smoothing length scale must be larger than " +
                         "the noise length scale.")

    if threshold is None:
        if cp.issubdtype(arr.dtype, cp.integer):
            threshold = 1
        else:
            threshold = 1/255.

    # Performance optimization: lowpass path can often be float32
    # but background boxcar (integer truncation) must stay in original dtype
    # for 1:1 accuracy alignment with CPU trackcupy.
    background = _boxcar_nearest(arr, llong)
    
    # We use float32 for lowpass to save bandwidth if input is not already high-precision
    lp_dtype = cp.float32 if arr.dtype in (cp.uint8, cp.uint16, cp.float32) else cp.float64
    result = _lowpass(arr, lshort, truncate, dtype=lp_dtype)
    
    result -= background.astype(lp_dtype, copy=False)

    # More memory efficient than cp.where
    cp.copyto(result, 0.0, where=(result < threshold))

    return result


def grey_dilation(image, separation, percentile=64, margin=None, precise=False):
    """GPU variant of find.grey_dilation that returns NumPy coordinates."""
    return asnumpy(gpu_grey_dilation(image, separation, percentile, margin, precise))


def gpu_grey_dilation(image, separation, percentile=64, margin=None, precise=False):
    """GPU variant of find.grey_dilation that returns CuPy coordinates."""
    cp = import_cupy()
    ndimage = _import_cupyx_ndimage()

    image = cp.asarray(image)
    ndim = image.ndim
    separation = _validate_tuple(separation, ndim)
    if margin is None:
        margin = tuple([int(s / 2) for s in separation])

    not_black = image[cp.nonzero(image)]
    if not_black.size == 0:
        warnings.warn("Image is completely black.", UserWarning)
        return cp.empty((0, ndim))
    threshold = cp.percentile(not_black, percentile)
    
    # Use float32 for dilation to save memory/speed if possible
    calc_dtype = cp.float32 if image.dtype in (cp.uint8, cp.uint16, cp.float32) else cp.float64
    image_f = image.astype(calc_dtype, copy=False)
    
    size = [int(2 * s / np.sqrt(ndim)) for s in separation]
    dilation = ndimage.grey_dilation(image_f, size=size, mode='constant')
    
    maxima_mask = (image_f == dilation) & (image_f > float(threshold))
    
    if int(cp.sum(maxima_mask).item()) == 0:
        warnings.warn("Image contains no local maxima.", UserWarning)
        return cp.empty((0, ndim))

    pos = cp.vstack(cp.where(maxima_mask)).T
    shape = cp.asarray(image.shape)
    margin_arr = cp.asarray(margin)
    near_edge = cp.any((pos < margin_arr) | (pos > (shape - margin_arr - 1)),
                       axis=1)
    pos = pos[~near_edge]

    if pos.shape[0] == 0:
        warnings.warn("All local maxima were in the margins.", UserWarning)
        return cp.empty((0, ndim))

    if precise:
        # precision drop_close is currently CPU-only in trackcupy
        pos_np = cp.asnumpy(pos)
        from .find import drop_close
        peak_values = cp.asnumpy(image[tuple(cp.asarray(pos_np).T)])
        pos_np = drop_close(pos_np, separation, peak_values)
        pos = cp.asarray(pos_np)
    return pos


_REFINE_KERNEL_SRC = r'''
#define FULL_MASK 0xffffffff
#define NAN_D (0.0 / 0.0)
#define NEG_INF_D (-1.0 / 0.0)

extern "C" __device__ __inline__ double warpReduceSum(double val) {
    for (int offset = 16; offset > 0; offset /= 2)
        val += __shfl_down_sync(FULL_MASK, val, offset);
    return val;
}

extern "C" __device__ __inline__ double warpReduceMax(double val) {
    for (int offset = 16; offset > 0; offset /= 2) {
        double other = __shfl_down_sync(FULL_MASK, val, offset);
        val = (val > other) ? val : other;
    }
    return val;
}

extern "C" __global__ void refine_com_arr_3d_kernel(
    const double* raw_image, const double* image,
    const int shape_z, const int shape_y, const int shape_x,
    const int radius_z, const int radius_y, const int radius_x,
    const int max_iterations, const double shift_thresh,
    const int characterize, const int isotropic,
    const int n_mask, const int* mask_z, const int* mask_y, const int* mask_x,
    const double* r2_mask, const double* z2_mask, const double* y2_mask, const double* x2_mask,
    const int* coords, const int out_cols, double* out, const int n_features)
{
    int feat = blockIdx.x;
    if (feat >= n_features) return;

    int lane = threadIdx.x; // Assumes blockDim.x == 32

    __shared__ double s_mass[32];
    __shared__ double s_cmz[32];
    __shared__ double s_cmy[32];
    __shared__ double s_cmx[32];
    
    // Characterization shares
    __shared__ double s_raw[32];
    __shared__ double s_a[32];
    __shared__ double s_b[32];
    __shared__ double s_c[32];
    __shared__ double s_max[32];

    int coord_z = coords[feat * 3 + 0];
    int coord_y = coords[feat * 3 + 1];
    int coord_x = coords[feat * 3 + 2];

    double cm_i_z, cm_i_y, cm_i_x;
    double last_mass = 0.0;
    int last_square_z, last_square_y, last_square_x;

    for (int iter = 0; iter < max_iterations; ++iter) {
        int eval_z = coord_z;
        int eval_y = coord_y;
        int eval_x = coord_x;
        int square_z = eval_z - radius_z;
        int square_y = eval_y - radius_y;
        int square_x = eval_x - radius_x;

        double partial_mass = 0.0;
        double partial_cmz = 0.0;
        double partial_cmy = 0.0;
        double partial_cmx = 0.0;

        for (int i = lane; i < n_mask; i += 32) {
            const int z = square_z + mask_z[i];
            const int y = square_y + mask_y[i];
            const int x = square_x + mask_x[i];
            const long long idx = ((long long)z * shape_y + y) * shape_x + x;
            const double px = (z >= 0 && z < shape_z && y >= 0 && y < shape_y && x >= 0 && x < shape_x) ? image[idx] : 0.0;
            partial_mass += px;
            partial_cmz += px * (double)mask_z[i];
            partial_cmy += px * (double)mask_y[i];
            partial_cmx += px * (double)mask_x[i];
        }

        s_mass[lane] = partial_mass;
        s_cmz[lane] = partial_cmz;
        s_cmy[lane] = partial_cmy;
        s_cmx[lane] = partial_cmx;

        double m = warpReduceSum(s_mass[lane]);
        double mz = warpReduceSum(s_cmz[lane]);
        double my = warpReduceSum(s_cmy[lane]);
        double mx = warpReduceSum(s_cmx[lane]);

        int done = 0;
        if (lane == 0) {
            s_mass[0] = m; s_cmz[0] = mz; s_cmy[0] = my; s_cmx[0] = mx;
            
            const double mass = m;
            last_mass = mass;
            last_square_z = square_z; last_square_y = square_y; last_square_x = square_x;

            if (mass <= 0.0) {
                cm_i_z = (double)eval_z; cm_i_y = (double)eval_y; cm_i_x = (double)eval_x;
                done = 1;
            } else {
                const double cm_n_z = mz / mass;
                const double cm_n_y = my / mass;
                const double cm_n_x = mx / mass;

                const double off_z = cm_n_z - (double)radius_z;
                const double off_y = cm_n_y - (double)radius_y;
                const double off_x = cm_n_x - (double)radius_x;

                cm_i_z = off_z + (double)eval_z;
                cm_i_y = off_y + (double)eval_y;
                cm_i_x = off_x + (double)eval_x;

                if (abs(off_z) < shift_thresh && abs(off_y) < shift_thresh && abs(off_x) < shift_thresh) {
                    done = 1;
                } else {
                    if (off_z > shift_thresh) coord_z++; else if (off_z < -shift_thresh) coord_z--;
                    if (off_y > shift_thresh) coord_y++; else if (off_y < -shift_thresh) coord_y--;
                    if (off_x > shift_thresh) coord_x++; else if (off_x < -shift_thresh) coord_x--;
                    
                    coord_z = (coord_z < radius_z) ? radius_z : (coord_z > shape_z - radius_z - 1 ? shape_z - radius_z - 1 : coord_z);
                    coord_y = (coord_y < radius_y) ? radius_y : (coord_y > shape_y - radius_y - 1 ? shape_y - radius_y - 1 : coord_y);
                    coord_x = (coord_x < radius_x) ? radius_x : (coord_x > shape_x - radius_x - 1 ? shape_x - radius_x - 1 : coord_x);
                }
            }
        }
        done = __shfl_sync(FULL_MASK, done, 0);
        coord_z = __shfl_sync(FULL_MASK, coord_z, 0);
        coord_y = __shfl_sync(FULL_MASK, coord_y, 0);
        coord_x = __shfl_sync(FULL_MASK, coord_x, 0);
        if (done) break;
    }

    if (lane == 0) {
        const int obase = feat * out_cols;
        out[obase + 0] = cm_i_z;
        out[obase + 1] = cm_i_y;
        out[obase + 2] = cm_i_x;
        out[obase + 3] = last_mass;
    }
    if (!characterize) return;

    if (last_mass <= 0.0) {
        if (lane == 0) {
            const int obase = feat * out_cols;
            if (isotropic) { out[obase+4]=NAN_D; out[obase+5]=NAN_D; out[obase+6]=0.0; out[obase+7]=0.0; }
            else { out[obase+4]=NAN_D; out[obase+5]=NAN_D; out[obase+6]=NAN_D; out[obase+7]=NAN_D; out[obase+8]=0.0; out[obase+9]=0.0; }
        }
        return;
    }

    double p_raw = 0.0, p_a = 0.0, p_b = 0.0, p_c = 0.0, p_max = NEG_INF_D;
    for (int i = lane; i < n_mask; i += 32) {
        const int z = last_square_z + mask_z[i];
        const int y = last_square_y + mask_y[i];
        const int x = last_square_x + mask_x[i];
        const long long idx = ((long long)z * shape_y + y) * shape_x + x;
        const double px = (z >= 0 && z < shape_z && y >= 0 && y < shape_y && x >= 0 && x < shape_x) ? image[idx] : 0.0;
        const double rx = (z >= 0 && z < shape_z && y >= 0 && y < shape_y && x >= 0 && x < shape_x) ? raw_image[idx] : 0.0;
        p_raw += rx;
        p_max = (px > p_max) ? px : p_max;
        if (isotropic) p_a += r2_mask[i] * px;
        else { p_a += z2_mask[i] * px; p_b += y2_mask[i] * px; p_c += x2_mask[i] * px; }
    }
    double m_raw = warpReduceSum(p_raw);
    double m_a = warpReduceSum(p_a);
    double m_b = warpReduceSum(p_b);
    double m_c = warpReduceSum(p_c);
    double m_max = warpReduceMax(p_max);

    if (lane == 0) {
        const int obase = feat * out_cols;
        if (isotropic) {
            out[obase + 4] = sqrt(m_a / last_mass);
            out[obase + 5] = NAN_D;
            out[obase + 6] = m_max;
            out[obase + 7] = m_raw;
        } else {
            out[obase + 4] = sqrt(m_a / last_mass);
            out[obase + 5] = sqrt(m_b / last_mass);
            out[obase + 6] = sqrt(m_c / last_mass);
            out[obase + 7] = NAN_D;
            out[obase + 8] = m_max;
            out[obase + 9] = m_raw;
        }
    }
}
'''


def _get_refine_kernel():
    cp = import_cupy()
    if not hasattr(_get_refine_kernel, "_kernel"):
        _get_refine_kernel._kernel = cp.RawKernel(
            _REFINE_KERNEL_SRC, "refine_com_arr_3d_kernel",
            options=("--std=c++11",)
        )
    return _get_refine_kernel._kernel


def refine_com_arr_3d(raw_image, image, radius, coords, max_iterations=10,
                      shift_thresh=0.6, characterize=True):
    """GPU-backed 3D center-of-mass refinement using RawKernel."""
    cp = import_cupy()

    raw_image_cp = cp.asarray(raw_image, dtype=cp.float64)
    image_cp = cp.asarray(image, dtype=cp.float64)
    coords_cp = cp.asarray(coords, dtype=cp.int32)
    radius = tuple(int(v) for v in radius)
    if len(radius) != 3:
        raise NotImplementedError("CuPy refinement currently supports 3D only.")

    n_features = coords_cp.shape[0]
    if n_features == 0:
        isotropic = (radius[0] == radius[1] == radius[2])
        return np.empty((0, (8 if isotropic else 10) if characterize else 4))

    isotropic = (radius[0] == radius[1] == radius[2])
    out_cols = (8 if isotropic else 10) if characterize else 4
    results_cp = cp.empty((n_features, out_cols), dtype=cp.float64)

    # Prepare masks
    from .masks import binary_mask
    mask = binary_mask(radius, 3)
    mask_z, mask_y, mask_x = mask.nonzero()
    mask_z_cp = cp.asarray(mask_z.astype(np.int32))
    mask_y_cp = cp.asarray(mask_y.astype(np.int32))
    mask_x_cp = cp.asarray(mask_x.astype(np.int32))

    points = [np.arange(-rad, rad + 1) for rad in radius]
    rel = np.array(np.meshgrid(*points, indexing="ij"))
    z2_mask_cp = cp.asarray((3 * rel[0] ** 2)[mask], dtype=cp.float64)
    y2_mask_cp = cp.asarray((3 * rel[1] ** 2)[mask], dtype=cp.float64)
    x2_mask_cp = cp.asarray((3 * rel[2] ** 2)[mask], dtype=cp.float64)
    r2_mask_cp = cp.asarray((rel[0] ** 2 + rel[1] ** 2 + rel[2] ** 2)[mask],
                            dtype=cp.float64)

    kernel = _get_refine_kernel()
    shape = image_cp.shape
    
    kernel(
        (n_features,), (32,),
        (raw_image_cp, image_cp,
         shape[0], shape[1], shape[2],
         radius[0], radius[1], radius[2],
         max_iterations, float(shift_thresh),
         int(characterize), int(isotropic),
         mask_z_cp.size, mask_z_cp, mask_y_cp, mask_x_cp,
         r2_mask_cp, z2_mask_cp, y2_mask_cp, x2_mask_cp,
         coords_cp.ravel(), out_cols, results_cp.ravel(), n_features)
    )
    
    return cp.asnumpy(results_cp)
