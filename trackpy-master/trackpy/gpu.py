import warnings

import numpy as np


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


def bandpass(image, lshort, llong, threshold=None, truncate=4):
    """GPU variant of preprocessing.bandpass that returns a NumPy array."""
    cp = import_cupy()
    ndimage = _import_cupyx_ndimage()

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

    background = arr.astype(cp.float64, copy=True)
    for axis, size in enumerate(llong):
        if size > 1:
            ndimage.uniform_filter1d(background, size, axis, output=background,
                                     mode='nearest', cval=0)

    result = arr.astype(cp.float64, copy=True)
    for axis, sigma in enumerate(lshort):
        if sigma > 0:
            kernel = cp.asarray(_gaussian_kernel(sigma, truncate))
            ndimage.correlate1d(result, kernel, axis, output=result,
                                mode='constant', cval=0.0)

    result -= background
    result = cp.where(result >= threshold, result, 0)
    return cp.asnumpy(result)


def grey_dilation(image, separation, percentile=64, margin=None, precise=False):
    """GPU variant of find.grey_dilation that returns NumPy coordinates."""
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
        return np.empty((0, ndim))
    threshold = cp.percentile(not_black, percentile)

    size = [int(2 * s / np.sqrt(ndim)) for s in separation]
    dilation = ndimage.grey_dilation(image, size=size, mode='constant')
    maxima = (image == dilation) & (image > threshold)
    if int(cp.sum(maxima).item()) == 0:
        warnings.warn("Image contains no local maxima.", UserWarning)
        return np.empty((0, ndim))

    pos = cp.vstack(cp.where(maxima)).T
    shape = cp.asarray(image.shape)
    margin_arr = cp.asarray(margin)
    near_edge = cp.any((pos < margin_arr) | (pos > (shape - margin_arr - 1)),
                       axis=1)
    pos = pos[~near_edge]

    if pos.shape[0] == 0:
        warnings.warn("All local maxima were in the margins.", UserWarning)
        return np.empty((0, ndim))

    pos = cp.asnumpy(pos)

    if precise:
        from .find import drop_close
        peak_values = cp.asnumpy(image[tuple(cp.asarray(pos).T)])
        pos = drop_close(pos, separation, peak_values)
    return pos


def _relative_coords(radius):
    points = [np.arange(-rad, rad + 1) for rad in radius]
    return np.array(np.meshgrid(*points, indexing="ij"))


def _binary_mask_np(radius):
    coords = _relative_coords(radius)
    terms = []
    for coord, rad in zip(coords, radius):
        if rad == 0:
            terms.append((coord != 0).astype(np.float64) * np.inf)
        else:
            terms.append((coord / rad) ** 2)
    return np.sum(terms, axis=0) <= 1


def refine_com_arr_3d(raw_image, image, radius, coords, max_iterations=10,
                      shift_thresh=0.6, characterize=True):
    """GPU-backed 3D center-of-mass refinement.

    Returns
    -------
    np.ndarray
        Compatible with trackpy.refine.center_of_mass.refine_com_arr output.
    """
    cp = import_cupy()

    raw_image = cp.asarray(raw_image)
    image = cp.asarray(image)
    coords = np.round(np.asarray(coords)).astype(int)
    radius = tuple(int(v) for v in radius)
    if len(radius) != 3:
        raise NotImplementedError("CuPy refinement currently supports 3D only.")

    ndim = 3
    N = coords.shape[0]
    isotropic = (radius[0] == radius[1] == radius[2])
    if characterize:
        cols = 8 if isotropic else 10
    else:
        cols = 4
    results = np.empty((N, cols), dtype=np.float64)

    mask = _binary_mask_np(radius)
    maskZ_idx, maskY_idx, maskX_idx = np.asarray(mask.nonzero(), dtype=np.int32)
    maskZ_idx_cp = cp.asarray(maskZ_idx)
    maskY_idx_cp = cp.asarray(maskY_idx)
    maskX_idx_cp = cp.asarray(maskX_idx)
    maskZ_idx_f = maskZ_idx_cp.astype(cp.float64)
    maskY_idx_f = maskY_idx_cp.astype(cp.float64)
    maskX_idx_f = maskX_idx_cp.astype(cp.float64)

    rel = _relative_coords(radius)
    z2_mask = cp.asarray((ndim * rel[0] ** 2)[mask], dtype=cp.float64)
    y2_mask = cp.asarray((ndim * rel[1] ** 2)[mask], dtype=cp.float64)
    x2_mask = cp.asarray((ndim * rel[2] ** 2)[mask], dtype=cp.float64)
    r2_mask = cp.asarray((rel[0] ** 2 + rel[1] ** 2 + rel[2] ** 2)[mask],
                         dtype=cp.float64)

    upper_bound = np.asarray(image.shape) - 1 - np.asarray(radius)
    radius_f = np.asarray(radius, dtype=np.float64)

    for feat in range(N):
        coordZ, coordY, coordX = (int(coords[feat, 0]),
                                  int(coords[feat, 1]),
                                  int(coords[feat, 2]))
        cm_i = np.asarray([coordZ, coordY, coordX], dtype=np.float64)
        px = None
        squareZ = squareY = squareX = 0
        mass_val = 0.0

        for _ in range(max_iterations):
            squareZ = coordZ - radius[0]
            squareY = coordY - radius[1]
            squareX = coordX - radius[2]
            px = image[squareZ + maskZ_idx_cp,
                       squareY + maskY_idx_cp,
                       squareX + maskX_idx_cp].astype(cp.float64)
            mass = px.sum()
            mass_val = float(mass.item())
            if mass_val == 0.0:
                cm_n = radius_f.copy()
            else:
                cm_n = np.asarray([
                    float((px * maskZ_idx_f).sum().item() / mass_val),
                    float((px * maskY_idx_f).sum().item() / mass_val),
                    float((px * maskX_idx_f).sum().item() / mass_val)
                ], dtype=np.float64)

            cm_i = cm_n - radius_f + np.asarray([coordZ, coordY, coordX],
                                                dtype=np.float64)
            off = cm_n - radius_f
            if np.all(np.abs(off) < shift_thresh):
                break

            if off[0] > shift_thresh:
                coordZ += 1
            elif off[0] < -shift_thresh:
                coordZ -= 1
            if off[1] > shift_thresh:
                coordY += 1
            elif off[1] < -shift_thresh:
                coordY -= 1
            if off[2] > shift_thresh:
                coordX += 1
            elif off[2] < -shift_thresh:
                coordX -= 1

            coordZ = int(np.clip(coordZ, radius[0], upper_bound[0]))
            coordY = int(np.clip(coordY, radius[1], upper_bound[1]))
            coordX = int(np.clip(coordX, radius[2], upper_bound[2]))

        results[feat, 0:3] = cm_i
        results[feat, 3] = mass_val
        if not characterize:
            continue

        if px is None:
            px = image[squareZ + maskZ_idx_cp,
                       squareY + maskY_idx_cp,
                       squareX + maskX_idx_cp].astype(cp.float64)

        if mass_val == 0.0:
            if isotropic:
                results[feat, 4] = np.nan
                results[feat, 5] = np.nan
                results[feat, 6] = np.nan
                results[feat, 7] = 0.0
            else:
                results[feat, 4:7] = np.nan
                results[feat, 7] = np.nan
                results[feat, 8] = 0.0
                results[feat, 9] = 0.0
            continue

        raw_px = raw_image[squareZ + maskZ_idx_cp,
                           squareY + maskY_idx_cp,
                           squareX + maskX_idx_cp].astype(cp.float64)
        signal = float(px.max().item())
        raw_mass = float(raw_px.sum().item())

        if isotropic:
            rg = float(cp.sqrt((r2_mask * px).sum() / mass_val).item())
            results[feat, 4] = rg
            results[feat, 5] = np.nan  # 3D ecc is undefined
            results[feat, 6] = signal
            results[feat, 7] = raw_mass
        else:
            rgz = float(cp.sqrt((z2_mask * px).sum() / mass_val).item())
            rgy = float(cp.sqrt((y2_mask * px).sum() / mass_val).item())
            rgx = float(cp.sqrt((x2_mask * px).sum() / mass_val).item())
            results[feat, 4] = rgz
            results[feat, 5] = rgy
            results[feat, 6] = rgx
            results[feat, 7] = np.nan  # 3D ecc is undefined
            results[feat, 8] = signal
            results[feat, 9] = raw_mass

    return results
