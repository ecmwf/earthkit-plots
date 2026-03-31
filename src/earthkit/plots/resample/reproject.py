import logging
import time

import numpy as np
from pyproj import Transformer
from scipy.interpolate import (
    LinearNDInterpolator,
    NearestNDInterpolator,
    RegularGridInterpolator,
)

logger = logging.getLogger(__name__)
ENABLE_TIMING = True

# Try to import CuPy for GPU acceleration
try:
    import cupy as cp
    from cupyx.scipy.interpolate import (
        RegularGridInterpolator as CuPyRegularGridInterpolator,
    )

    HAS_CUPY = True
    logger.info("CuPy detected - GPU acceleration available for reprojection")
except ImportError:
    cp = None
    CuPyRegularGridInterpolator = None
    HAS_CUPY = False

# Global setting for GPU acceleration (can be enabled/disabled at runtime)
USE_GPU = False  # Default to CPU for compatibility

# Cache for expensive Transformer objects
# Key format: (src_crs_class_name, target_crs_class_name, src_crs_params, target_crs_params)
_TRANSFORMER_CACHE = {}


def enable_gpu_acceleration():
    """
    Enable GPU acceleration for reprojection.

    Requires CuPy to be installed. If CuPy is not available, this will have no effect.
    """
    global USE_GPU
    if HAS_CUPY:
        USE_GPU = True
        logger.info("GPU acceleration ENABLED for reprojection")
    else:
        logger.warning(
            "GPU acceleration requested but CuPy is not available. Install cupy to enable GPU support."
        )


def disable_gpu_acceleration():
    """Disable GPU acceleration for reprojection (use CPU)."""
    global USE_GPU
    USE_GPU = False
    logger.info("GPU acceleration DISABLED for reprojection")


def _get_crs_cache_key(crs):
    """
    Generate a hashable cache key for a CRS object.

    Uses the WKT representation, which is stable across instances and works for
    all CRS types without needing per-projection special cases.
    """
    return crs.to_wkt()


def _get_cached_transformer(crs_src, crs_target):
    """
    Get a cached Transformer or create and cache a new one.

    Creating Transformer objects is very expensive (100-300ms), so we cache them
    based on CRS types and parameters.
    """
    # Generate cache keys for both CRS objects
    src_key = _get_crs_cache_key(crs_src)
    tgt_key = _get_crs_cache_key(crs_target)
    cache_key = (src_key, tgt_key)

    # Check if we have a cached transformer
    if cache_key not in _TRANSFORMER_CACHE:
        # Create new transformer and cache it
        transformer = Transformer.from_crs(crs_target, crs_src, always_xy=True)
        _TRANSFORMER_CACHE[cache_key] = transformer
        if ENABLE_TIMING:
            logger.info(
                f"  [TIMING] reproject: Created NEW transformer for {type(crs_src).__name__} → {type(crs_target).__name__} (cache size: {len(_TRANSFORMER_CACHE)})"
            )
    else:
        if ENABLE_TIMING:
            logger.info(
                f"  [TIMING] reproject: Using CACHED transformer for {type(crs_src).__name__} → {type(crs_target).__name__}"
            )

    return _TRANSFORMER_CACHE[cache_key]


def _transform_coordinates_parallel(transformer, x_tgt, y_tgt, num_chunks=4):
    """
    Transform coordinates in parallel chunks.

    Splits the grid into chunks and transforms them concurrently using threading.
    This can provide speedup for large grids since pyproj releases the GIL.

    Parameters
    ----------
    transformer : Transformer
        The pyproj transformer
    x_tgt, y_tgt : ndarray
        Target coordinates (2D arrays)
    num_chunks : int
        Number of chunks to split the work into (default: 4)

    Returns
    -------
    x_src_reproj, y_src_reproj : ndarray
        Transformed coordinates
    """
    from concurrent.futures import ThreadPoolExecutor

    import numpy as np

    ny, nx = x_tgt.shape
    chunk_size = max(1, ny // num_chunks)

    def transform_chunk(start_idx, end_idx):
        x_chunk = x_tgt[start_idx:end_idx, :]
        y_chunk = y_tgt[start_idx:end_idx, :]
        return transformer.transform(x_chunk, y_chunk)

    # Create chunk ranges
    chunks = [
        (i * chunk_size, min((i + 1) * chunk_size, ny)) for i in range(num_chunks)
    ]

    # Transform chunks in parallel
    with ThreadPoolExecutor(max_workers=num_chunks) as executor:
        results = list(executor.map(lambda chunk: transform_chunk(*chunk), chunks))

    # Concatenate results
    x_src_reproj = np.vstack([r[0] for r in results])
    y_src_reproj = np.vstack([r[1] for r in results])

    return x_src_reproj, y_src_reproj


def reproject_to_grid(
    x_src,
    y_src,
    z_src,
    crs_src,
    bbox_target,
    crs_target,
    nx=500,
    ny=500,
    use_gpu=None,
    method="linear",
):
    """
    Reproject a scalar field from its source CRS onto a regular grid in a target CRS,
    with support for periodic longitude wrapping.

    Parameters
    ----------
    x_src : ndarray
        Source x coordinates (1D or 2D)
    y_src : ndarray
        Source y coordinates (1D or 2D)
    z_src : ndarray
        Source data values (2D)
    crs_src : cartopy.crs.CRS
        Source coordinate reference system
    bbox_target : tuple
        Target bounding box (xmin, xmax, ymin, ymax)
    crs_target : cartopy.crs.CRS
        Target coordinate reference system
    nx : int, optional
        Number of points in x direction for output grid (default: 500)
    ny : int, optional
        Number of points in y direction for output grid (default: 500)
    use_gpu : bool, optional
        Whether to use GPU acceleration (requires CuPy). If None, uses global USE_GPU setting.

    Returns
    -------
    x_tgt : ndarray
        Target x coordinates (2D)
    y_tgt : ndarray
        Target y coordinates (2D)
    z_tgt : ndarray
        Reprojected data values (2D)
    """
    t_start = time.time() if ENABLE_TIMING else None

    # Determine whether to use GPU
    gpu_enabled = USE_GPU if use_gpu is None else use_gpu
    if gpu_enabled and not HAS_CUPY:
        logger.warning("GPU requested but CuPy not available, falling back to CPU")
        gpu_enabled = False

    if ENABLE_TIMING and gpu_enabled:
        logger.info("  [TIMING] reproject: Using GPU acceleration")

    # Choose array library based on GPU setting
    xp = cp if gpu_enabled else np

    # Build output grid in target CRS
    t0 = time.time() if ENABLE_TIMING else None
    xmin, xmax, ymin, ymax = bbox_target
    x_tgt_1d = xp.linspace(xmin, xmax, nx)
    y_tgt_1d = xp.linspace(ymin, ymax, ny)
    x_tgt, y_tgt = xp.meshgrid(x_tgt_1d, y_tgt_1d)
    if ENABLE_TIMING:
        logger.info(
            f"  [TIMING] reproject: Build target grid: {(time.time() - t0) * 1000:.2f}ms"
        )

    # Get cached transformer: target CRS → source CRS
    # This is expensive (100-300ms) so we cache transformers by CRS type + parameters
    t0 = time.time() if ENABLE_TIMING else None
    transformer = _get_cached_transformer(crs_src, crs_target)
    if ENABLE_TIMING:
        logger.info(
            f"  [TIMING] reproject: Get/create transformer: {(time.time() - t0) * 1000:.2f}ms"
        )

    # Transform the target grid into source coordinates
    # Note: pyproj transformer works with CPU arrays, so convert if using GPU
    # Use parallel transformation for large grids (pyproj releases GIL)
    t0 = time.time() if ENABLE_TIMING else None
    grid_size = nx * ny
    use_parallel = grid_size > 100000  # Use parallel for grids larger than 100k points

    if gpu_enabled:
        # Convert to CPU for transformation, then back to GPU
        x_tgt_cpu = cp.asnumpy(x_tgt)
        y_tgt_cpu = cp.asnumpy(y_tgt)
        if use_parallel:
            x_src_reproj_cpu, y_src_reproj_cpu = _transform_coordinates_parallel(
                transformer, x_tgt_cpu, y_tgt_cpu
            )
            if ENABLE_TIMING:
                logger.info(
                    f"  [TIMING] reproject: Transform coordinates (parallel, {grid_size} points): {(time.time() - t0) * 1000:.2f}ms"
                )
        else:
            x_src_reproj_cpu, y_src_reproj_cpu = transformer.transform(
                x_tgt_cpu, y_tgt_cpu
            )
            if ENABLE_TIMING:
                logger.info(
                    f"  [TIMING] reproject: Transform coordinates (serial, {grid_size} points): {(time.time() - t0) * 1000:.2f}ms"
                )
        x_src_reproj = cp.asarray(x_src_reproj_cpu)
        y_src_reproj = cp.asarray(y_src_reproj_cpu)
    else:
        if use_parallel:
            x_src_reproj, y_src_reproj = _transform_coordinates_parallel(
                transformer, x_tgt, y_tgt
            )
            if ENABLE_TIMING:
                logger.info(
                    f"  [TIMING] reproject: Transform coordinates (parallel, {grid_size} points): {(time.time() - t0) * 1000:.2f}ms"
                )
        else:
            x_src_reproj, y_src_reproj = transformer.transform(x_tgt, y_tgt)
            if ENABLE_TIMING:
                logger.info(
                    f"  [TIMING] reproject: Transform coordinates (serial, {grid_size} points): {(time.time() - t0) * 1000:.2f}ms"
                )

    # Interpolation
    # Transfer source data to GPU if needed
    t0 = time.time() if ENABLE_TIMING else None
    if gpu_enabled:
        x_src_gpu = cp.asarray(x_src)
        y_src_gpu = cp.asarray(y_src)
        z_src_gpu = cp.asarray(z_src)
    else:
        x_src_gpu = x_src
        y_src_gpu = y_src
        z_src_gpu = z_src

    if x_src.ndim == 1 and y_src.ndim == 1 and z_src.ndim == 2:
        # Ensure x_src and y_src are strictly monotonically ascending — required
        # by RegularGridInterpolator.  Domain extraction or unusual data ordering
        # can produce non-monotonic arrays (e.g. [0, ..., 180, -179, ..., -1]).
        # Sort both axes and reorder z accordingly, then drop any duplicate
        # coordinate values (e.g. -180 == 180 appearing twice after wrapping).
        x_order = np.argsort(x_src)
        y_order = np.argsort(y_src)
        x_src = x_src[x_order]
        y_src = y_src[y_order]
        z_src = z_src[np.ix_(y_order, x_order)]

        # Remove duplicate x values (keep first occurrence after sort)
        x_unique_mask = np.concatenate(([True], np.diff(x_src) > 1e-10))
        y_unique_mask = np.concatenate(([True], np.diff(y_src) > 1e-10))
        if not x_unique_mask.all():
            x_src = x_src[x_unique_mask]
            z_src = z_src[:, x_unique_mask]
        if not y_unique_mask.all():
            y_src = y_src[y_unique_mask]
            z_src = z_src[y_unique_mask, :]

        # Update GPU aliases to reflect the sorted/deduplicated arrays
        if gpu_enabled:
            x_src_gpu = cp.asarray(x_src)
            y_src_gpu = cp.asarray(y_src)
            z_src_gpu = cp.asarray(z_src)
        else:
            x_src_gpu = x_src
            y_src_gpu = y_src
            z_src_gpu = z_src

        # ------- Handle periodic longitude -------
        # Detect if x_src spans ~360°.
        # Many datasets use non-inclusive endpoints (e.g. [-180, ..., 179] or
        # [0, ..., 359]) so we check both the actual span and the span including
        # one extra grid step.  Both cases are treated as globally periodic.
        #
        # Guard: only apply for geographic (degree-range) coordinates.  Projected
        # CRS coordinates in metres (e.g. LAEA, UTM) can have spans that are
        # coincidentally divisible by 360, which would trigger spurious modulo
        # normalisation and scramble the interpolation.
        x_diff = float(x_src[-1] - x_src[0])
        dx = float(x_src[1] - x_src[0]) if len(x_src) > 1 else 0.0
        _span_with_step = x_diff + dx  # span if the endpoint were included
        _looks_geographic = float(x_src[0]) >= -360.0 and float(x_src[-1]) <= 360.0
        is_periodic = _looks_geographic and (
            np.isclose(x_diff % 360, 0, atol=1e-3)
            or np.isclose(_span_with_step % 360, 0, atol=1e-3)
            or np.isclose(x_diff % (2 * np.pi), 0, atol=1e-5)
            or np.isclose(_span_with_step % (2 * np.pi), 0, atol=1e-5)
        )
        # Always use the full 360° period for modulo normalisation so that
        # target coordinates from any longitude convention are correctly
        # wrapped back into the source domain.
        if is_periodic:
            x_diff = 360.0

        if is_periodic:
            t1 = time.time() if ENABLE_TIMING else None
            # Normalize transformed coordinates to same domain as x_src
            x0 = x_src[0]

            x_reproj_norm = (x_src_reproj - x0) % x_diff + x0
            if ENABLE_TIMING:
                logger.info(
                    f"  [TIMING] reproject: Coordinate normalization (NumPy): {(time.time() - t1) * 1000:.2f}ms"
                )

            # Extend source arrays for seamless interpolation
            x_ext = xp.hstack(
                [
                    x_src_gpu[0] - (x_src_gpu[1] - x_src_gpu[0]),
                    x_src_gpu,
                    x_src_gpu[-1] + (x_src_gpu[1] - x_src_gpu[0]),
                ]
            )

            z_ext = xp.hstack(
                [
                    z_src_gpu[:, -1][:, None],  # last column appended left
                    z_src_gpu,
                    z_src_gpu[:, 0][:, None],
                ]
            )  # first column appended right
            if ENABLE_TIMING:
                logger.info(
                    f"  [TIMING] reproject: Prepare periodic wrapping: {(time.time() - t1) * 1000:.2f}ms"
                )

            t1 = time.time() if ENABLE_TIMING else None
            if gpu_enabled:
                # CuPy RegularGridInterpolator
                # Note: cupyx.scipy.interpolate requires CPU arrays for coordinates, GPU for values
                interp = CuPyRegularGridInterpolator(
                    (cp.asnumpy(y_src_gpu), cp.asnumpy(x_ext)),
                    z_ext,
                    bounds_error=False,
                    fill_value=float("nan"),
                )
                pts = xp.column_stack([y_src_reproj.ravel(), x_reproj_norm.ravel()])
                z_tgt = interp(cp.asnumpy(pts)).reshape(ny, nx)
            else:
                interp = RegularGridInterpolator(
                    (y_src_gpu, x_ext), z_ext, bounds_error=False, fill_value=np.nan
                )
                pts = xp.column_stack([y_src_reproj.ravel(), x_reproj_norm.ravel()])
                z_tgt = interp(pts).reshape(ny, nx)
            if ENABLE_TIMING:
                device_str = "GPU" if gpu_enabled else "CPU"
                logger.info(
                    f"  [TIMING] reproject: RegularGridInterpolator ({device_str}, periodic): {(time.time() - t1) * 1000:.2f}ms"
                )

        else:
            # Non-periodic case
            t1 = time.time() if ENABLE_TIMING else None
            if gpu_enabled:
                # CuPy RegularGridInterpolator
                interp = CuPyRegularGridInterpolator(
                    (cp.asnumpy(y_src_gpu), cp.asnumpy(x_src_gpu)),
                    z_src_gpu,
                    bounds_error=False,
                    fill_value=float("nan"),
                )
                pts = xp.column_stack([y_src_reproj.ravel(), x_src_reproj.ravel()])
                z_tgt = interp(cp.asnumpy(pts)).reshape(ny, nx)
            else:
                interp = RegularGridInterpolator(
                    (y_src_gpu, x_src_gpu),
                    z_src_gpu,
                    bounds_error=False,
                    fill_value=np.nan,
                )
                pts = xp.column_stack([y_src_reproj.ravel(), x_src_reproj.ravel()])
                z_tgt = interp(pts).reshape(ny, nx)
            if ENABLE_TIMING:
                device_str = "GPU" if gpu_enabled else "CPU"
                logger.info(
                    f"  [TIMING] reproject: RegularGridInterpolator ({device_str}, non-periodic): {(time.time() - t1) * 1000:.2f}ms"
                )

    else:
        # Curvilinear grid → need scattered interpolation
        # GPU doesn't support LinearNDInterpolator well, so fall back to CPU
        t1 = time.time() if ENABLE_TIMING else None
        if gpu_enabled:
            logger.warning(
                "GPU acceleration not supported for curvilinear grids, falling back to CPU for interpolation"
            )
            x_src_cpu = cp.asnumpy(x_src_gpu) if gpu_enabled else x_src_gpu
            y_src_cpu = cp.asnumpy(y_src_gpu) if gpu_enabled else y_src_gpu
            z_src_cpu = cp.asnumpy(z_src_gpu) if gpu_enabled else z_src_gpu
            x_src_reproj_cpu = cp.asnumpy(x_src_reproj)
            y_src_reproj_cpu = cp.asnumpy(y_src_reproj)
        else:
            x_src_cpu = x_src_gpu
            y_src_cpu = y_src_gpu
            z_src_cpu = z_src_gpu
            x_src_reproj_cpu = x_src_reproj
            y_src_reproj_cpu = y_src_reproj

        src_points = np.column_stack([x_src_cpu.flatten(), y_src_cpu.flatten()])
        pts = np.column_stack([x_src_reproj_cpu.ravel(), y_src_reproj_cpu.ravel()])
        if method == "nearest":
            interp = NearestNDInterpolator(src_points, z_src_cpu.flatten())
        else:
            interp = LinearNDInterpolator(
                src_points, z_src_cpu.flatten(), fill_value=np.nan
            )
        z_tgt_cpu = interp(pts).reshape(ny, nx)

        # Convert back to GPU if needed
        z_tgt = cp.asarray(z_tgt_cpu) if gpu_enabled else z_tgt_cpu
        if ENABLE_TIMING:
            interp_name = (
                "NearestNDInterpolator"
                if method == "nearest"
                else "LinearNDInterpolator"
            )
            logger.info(
                f"  [TIMING] reproject: {interp_name} (scattered, CPU): {(time.time() - t1) * 1000:.2f}ms"
            )

    if ENABLE_TIMING:
        logger.info(
            f"  [TIMING] reproject: TOTAL interpolation: {(time.time() - t0) * 1000:.2f}ms"
        )

    # Convert GPU arrays back to CPU for return
    if gpu_enabled:
        t0 = time.time() if ENABLE_TIMING else None
        x_tgt = cp.asnumpy(x_tgt)
        y_tgt = cp.asnumpy(y_tgt)
        z_tgt = cp.asnumpy(z_tgt)
        if ENABLE_TIMING:
            logger.info(
                f"  [TIMING] reproject: GPU→CPU transfer: {(time.time() - t0) * 1000:.2f}ms"
            )

    if ENABLE_TIMING:
        logger.info(
            f"  [TIMING] reproject: === TOTAL reproject_to_grid: {(time.time() - t_start) * 1000:.2f}ms ==="
        )

    return x_tgt, y_tgt, z_tgt


def _reproject_nn(
    x_src_1d,
    y_src_1d,
    z_src,
    crs_src,
    bbox_target,
    crs_target,
    nx=1000,
    ny=1000,
):
    """
    Render a regular rectilinear source grid onto an nx×ny pixel image by
    nearest-neighbour cell lookup.

    For each pixel in the output image (in the target CRS) the pixel centre is
    back-transformed to the source CRS; the nearest source row and column are
    found with :func:`numpy.searchsorted` on the 1-D source axes; and the
    corresponding data value is assigned to that pixel.

    This is O(nx×ny) and produces crisp cell-boundary edges with no
    interpolation blurring — equivalent to the approach used by
    :func:`~earthkit.plots.resample.healpix.nnshow` and
    :func:`~earthkit.plots.resample.octahedral.nnshow` but generalised to arbitrary
    regular rectilinear source grids.

    Parameters
    ----------
    x_src_1d : 1-D ndarray
        Source x-coordinate (longitude) axis.  May be ascending or descending.
    y_src_1d : 1-D ndarray
        Source y-coordinate (latitude) axis.  May be ascending or descending.
    z_src : 2-D ndarray, shape ``(len(y_src_1d), len(x_src_1d))``
        Source data values.
    crs_src : cartopy.crs.CRS
        Coordinate reference system of the source data.
    bbox_target : tuple
        ``(xmin, xmax, ymin, ymax)`` in target CRS units.
    crs_target : cartopy.crs.CRS
        Target (map) coordinate reference system.
    nx : int, optional
        Number of output pixels in the x direction (default 1000).
    ny : int, optional
        Number of output pixels in the y direction (default 1000).

    Returns
    -------
    image : 2-D ndarray, shape ``(ny, nx)``
        Pixel image; NaN where back-transformation falls outside the source
        domain or produces non-finite coordinates.
    extent : tuple
        ``(xmin, xmax, ymin, ymax)`` for use with
        :func:`matplotlib.axes.Axes.imshow`.
    """
    xmin, xmax, ymin, ymax = bbox_target

    # Build output pixel-centre coordinates in the target CRS
    dx = (xmax - xmin) / nx
    dy = (ymax - ymin) / ny
    x_pix = np.linspace(xmin + dx / 2, xmax - dx / 2, nx)
    y_pix = np.linspace(ymin + dy / 2, ymax - dy / 2, ny)
    x_pix2, y_pix2 = np.meshgrid(x_pix, y_pix)

    # Back-transform pixel centres into the source CRS
    transformer = _get_cached_transformer(crs_src, crs_target)
    x_src_reproj, y_src_reproj = transformer.transform(x_pix2, y_pix2)

    # Work with sorted ascending axes for searchsorted; remember if we flipped
    x_flip = bool(x_src_1d[-1] < x_src_1d[0])
    y_flip = bool(y_src_1d[-1] < y_src_1d[0])
    x_sorted = x_src_1d[::-1] if x_flip else x_src_1d
    y_sorted = y_src_1d[::-1] if y_flip else y_src_1d

    # Handle longitude periodicity: wrap back-transformed lons into the source domain
    x_span = float(x_sorted[-1] - x_sorted[0])
    x_step = float(x_sorted[1] - x_sorted[0]) if len(x_sorted) > 1 else 0.0
    is_periodic = np.isclose((x_span + x_step) % 360, 0, atol=1e-3)
    if is_periodic:
        x_src_reproj = (x_src_reproj - float(x_sorted[0])) % 360.0 + float(x_sorted[0])

    # Nearest-neighbour lookup: each pixel maps to the source cell whose centre
    # is closest.  searchsorted gives the right-insertion index; subtracting 1
    # gives the cell to the left of the pixel, then we clamp to the valid range.
    col_idx = np.searchsorted(x_sorted, x_src_reproj) - 1
    row_idx = np.searchsorted(y_sorted, y_src_reproj) - 1
    col_idx = np.clip(col_idx, 0, len(x_sorted) - 1)
    row_idx = np.clip(row_idx, 0, len(y_sorted) - 1)

    # If the original axis was descending, the sorted index runs in the opposite
    # direction — flip back so it indexes into the original z_src correctly.
    if x_flip:
        col_idx = (len(x_src_1d) - 1) - col_idx
    if y_flip:
        row_idx = (len(y_src_1d) - 1) - row_idx

    # Assemble the output image; NaN-fill pixels with non-finite back-projections
    image = z_src[row_idx, col_idx].astype(float)
    invalid = ~np.isfinite(x_src_reproj) | ~np.isfinite(y_src_reproj)
    image[invalid] = np.nan

    return image, (xmin, xmax, ymin, ymax)
