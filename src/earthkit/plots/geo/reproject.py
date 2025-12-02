import numpy as np
import time
import logging
from pyproj import Transformer
from scipy.interpolate import RegularGridInterpolator, LinearNDInterpolator

logger = logging.getLogger(__name__)
ENABLE_TIMING = True

# Try to import Numba for JIT compilation
try:
    from numba import jit
    HAS_NUMBA = True
except ImportError:
    # Create a no-op decorator if Numba is not available
    def jit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if args and callable(args[0]) else decorator
    HAS_NUMBA = False

# Try to import CuPy for GPU acceleration
try:
    import cupy as cp
    from cupyx.scipy.interpolate import RegularGridInterpolator as CuPyRegularGridInterpolator
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

# JIT-compiled helper functions for performance-critical operations
@jit(nopython=True, cache=True)
def _normalize_periodic_coords_jit(x_reproj_flat, x0, x_diff):
    """
    JIT-compiled periodic coordinate normalization.

    Normalizes coordinates to the source domain for periodic (global) grids.
    This is a hot path that benefits significantly from JIT compilation.
    """
    return (x_reproj_flat - x0) % x_diff + x0

@jit(nopython=True, cache=True, parallel=True)
def _normalize_periodic_coords_parallel(x_reproj_flat, x0, x_diff):
    """
    Parallel JIT-compiled periodic coordinate normalization.

    Uses Numba's parallel execution for large arrays.
    """
    result = np.empty_like(x_reproj_flat)
    for i in range(x_reproj_flat.size):
        result.flat[i] = (x_reproj_flat.flat[i] - x0) % x_diff + x0
    return result

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
        logger.warning("GPU acceleration requested but CuPy is not available. Install cupy to enable GPU support.")

def disable_gpu_acceleration():
    """Disable GPU acceleration for reprojection (use CPU)."""
    global USE_GPU
    USE_GPU = False
    logger.info("GPU acceleration DISABLED for reprojection")

def _get_crs_cache_key(crs):
    """
    Generate a hashable cache key for a CRS object.

    For common CRS types, we use class name + key parameters.
    This allows us to cache transformers for identical CRS configurations.
    """
    crs_class = type(crs).__name__

    # For common CRS types, extract key parameters that define uniqueness
    if crs_class == 'NorthPolarStereo':
        # North Polar Stereo is defined by central longitude and true scale latitude
        central_lon = getattr(crs, 'proj4_params', {}).get('lon_0', 0)
        true_scale = getattr(crs, 'proj4_params', {}).get('lat_ts', 90)
        return (crs_class, central_lon, true_scale)

    elif crs_class == 'SouthPolarStereo':
        # South Polar Stereo is defined by central longitude and true scale latitude
        central_lon = getattr(crs, 'proj4_params', {}).get('lon_0', 0)
        true_scale = getattr(crs, 'proj4_params', {}).get('lat_ts', -90)
        return (crs_class, central_lon, true_scale)

    elif crs_class == 'PlateCarree':
        # PlateCarree has no parameters - all instances are equivalent
        return (crs_class,)

    elif crs_class == 'LambertConformal':
        # Lambert Conformal defined by central lon/lat and standard parallels
        central_lon = getattr(crs, 'proj4_params', {}).get('lon_0', 0)
        central_lat = getattr(crs, 'proj4_params', {}).get('lat_0', 0)
        std_parallels = getattr(crs, 'proj4_params', {}).get('lat_1', None)
        return (crs_class, central_lon, central_lat, std_parallels)

    elif crs_class == 'Orthographic':
        # Orthographic defined by central lon/lat
        central_lon = getattr(crs, 'proj4_params', {}).get('lon_0', 0)
        central_lat = getattr(crs, 'proj4_params', {}).get('lat_0', 0)
        return (crs_class, central_lon, central_lat)

    # For unknown CRS types, use object id (won't cache across different instances)
    # This is safe but won't benefit from caching
    return (crs_class, id(crs))

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
            logger.info(f"  [TIMING] reproject: Created NEW transformer for {type(crs_src).__name__} → {type(crs_target).__name__} (cache size: {len(_TRANSFORMER_CACHE)})")
    else:
        if ENABLE_TIMING:
            logger.info(f"  [TIMING] reproject: Using CACHED transformer for {type(crs_src).__name__} → {type(crs_target).__name__}")

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
    chunks = [(i * chunk_size, min((i + 1) * chunk_size, ny)) for i in range(num_chunks)]

    # Transform chunks in parallel
    with ThreadPoolExecutor(max_workers=num_chunks) as executor:
        results = list(executor.map(lambda chunk: transform_chunk(*chunk), chunks))

    # Concatenate results
    x_src_reproj = np.vstack([r[0] for r in results])
    y_src_reproj = np.vstack([r[1] for r in results])

    return x_src_reproj, y_src_reproj

def reproject_to_grid(
    x_src, y_src, z_src, crs_src,
    bbox_target, crs_target,
    nx=500, ny=500,
    use_gpu=None,
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
        logger.info(f"  [TIMING] reproject: Using GPU acceleration")

    # Choose array library based on GPU setting
    xp = cp if gpu_enabled else np

    # Build output grid in target CRS
    t0 = time.time() if ENABLE_TIMING else None
    xmin, xmax, ymin, ymax = bbox_target
    x_tgt_1d = xp.linspace(xmin, xmax, nx)
    y_tgt_1d = xp.linspace(ymin, ymax, ny)
    x_tgt, y_tgt = xp.meshgrid(x_tgt_1d, y_tgt_1d)
    if ENABLE_TIMING:
        logger.info(f"  [TIMING] reproject: Build target grid: {(time.time() - t0)*1000:.2f}ms")

    # Get cached transformer: target CRS → source CRS
    # This is expensive (100-300ms) so we cache transformers by CRS type + parameters
    t0 = time.time() if ENABLE_TIMING else None
    transformer = _get_cached_transformer(crs_src, crs_target)
    if ENABLE_TIMING:
        logger.info(f"  [TIMING] reproject: Get/create transformer: {(time.time() - t0)*1000:.2f}ms")

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
            x_src_reproj_cpu, y_src_reproj_cpu = _transform_coordinates_parallel(transformer, x_tgt_cpu, y_tgt_cpu)
            if ENABLE_TIMING:
                logger.info(f"  [TIMING] reproject: Transform coordinates (parallel, {grid_size} points): {(time.time() - t0)*1000:.2f}ms")
        else:
            x_src_reproj_cpu, y_src_reproj_cpu = transformer.transform(x_tgt_cpu, y_tgt_cpu)
            if ENABLE_TIMING:
                logger.info(f"  [TIMING] reproject: Transform coordinates (serial, {grid_size} points): {(time.time() - t0)*1000:.2f}ms")
        x_src_reproj = cp.asarray(x_src_reproj_cpu)
        y_src_reproj = cp.asarray(y_src_reproj_cpu)
    else:
        if use_parallel:
            x_src_reproj, y_src_reproj = _transform_coordinates_parallel(transformer, x_tgt, y_tgt)
            if ENABLE_TIMING:
                logger.info(f"  [TIMING] reproject: Transform coordinates (parallel, {grid_size} points): {(time.time() - t0)*1000:.2f}ms")
        else:
            x_src_reproj, y_src_reproj = transformer.transform(x_tgt, y_tgt)
            if ENABLE_TIMING:
                logger.info(f"  [TIMING] reproject: Transform coordinates (serial, {grid_size} points): {(time.time() - t0)*1000:.2f}ms")

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

    if x_src.ndim == 1 and y_src.ndim == 1:
        # ------- Handle periodic longitude -------
        # Detect if x_src spans ~360° or ~2π
        x_diff = x_src[-1] - x_src[0]
        is_periodic = np.isclose(x_diff % 360, 0, atol=1e-6) or np.isclose(x_diff % (2*np.pi), 0, atol=1e-6)

        if is_periodic:
            t1 = time.time() if ENABLE_TIMING else None
            # Normalize transformed coordinates to same domain as x_src
            x0 = x_src[0]

            # Use JIT-compiled normalization if Numba is available and array is large
            if HAS_NUMBA and x_src_reproj.size > 10000:
                # For large arrays, use parallel JIT version
                x_reproj_norm = _normalize_periodic_coords_parallel(x_src_reproj, x0, x_diff)
                if ENABLE_TIMING:
                    logger.info(f"  [TIMING] reproject: Coordinate normalization (Numba parallel JIT): {(time.time() - t1)*1000:.2f}ms")
            elif HAS_NUMBA:
                # For smaller arrays, use single-threaded JIT version
                x_reproj_norm = _normalize_periodic_coords_jit(x_src_reproj, x0, x_diff)
                if ENABLE_TIMING:
                    logger.info(f"  [TIMING] reproject: Coordinate normalization (Numba JIT): {(time.time() - t1)*1000:.2f}ms")
            else:
                # Fallback to regular NumPy
                x_reproj_norm = (x_src_reproj - x0) % x_diff + x0
                if ENABLE_TIMING:
                    logger.info(f"  [TIMING] reproject: Coordinate normalization (NumPy): {(time.time() - t1)*1000:.2f}ms")

            # Extend source arrays for seamless interpolation
            x_ext = xp.hstack([x_src_gpu[0] - (x_src_gpu[1] - x_src_gpu[0]),
                               x_src_gpu,
                               x_src_gpu[-1] + (x_src_gpu[1] - x_src_gpu[0])])

            z_ext = xp.hstack([z_src_gpu[:, -1][:, None],  # last column appended left
                               z_src_gpu,
                               z_src_gpu[:, 0][:, None]])  # first column appended right
            if ENABLE_TIMING:
                logger.info(f"  [TIMING] reproject: Prepare periodic wrapping: {(time.time() - t1)*1000:.2f}ms")

            t1 = time.time() if ENABLE_TIMING else None
            if gpu_enabled:
                # CuPy RegularGridInterpolator
                # Note: cupyx.scipy.interpolate requires CPU arrays for coordinates, GPU for values
                interp = CuPyRegularGridInterpolator(
                    (cp.asnumpy(y_src_gpu), cp.asnumpy(x_ext)),
                    z_ext,
                    bounds_error=False,
                    fill_value=float('nan')
                )
                pts = xp.column_stack([y_src_reproj.ravel(), x_reproj_norm.ravel()])
                z_tgt = interp(cp.asnumpy(pts)).reshape(ny, nx)
            else:
                interp = RegularGridInterpolator(
                    (y_src_gpu, x_ext),
                    z_ext,
                    bounds_error=False,
                    fill_value=np.nan
                )
                pts = xp.column_stack([y_src_reproj.ravel(), x_reproj_norm.ravel()])
                z_tgt = interp(pts).reshape(ny, nx)
            if ENABLE_TIMING:
                device_str = "GPU" if gpu_enabled else "CPU"
                logger.info(f"  [TIMING] reproject: RegularGridInterpolator ({device_str}, periodic): {(time.time() - t1)*1000:.2f}ms")

        else:
            # Non-periodic case
            t1 = time.time() if ENABLE_TIMING else None
            if gpu_enabled:
                # CuPy RegularGridInterpolator
                interp = CuPyRegularGridInterpolator(
                    (cp.asnumpy(y_src_gpu), cp.asnumpy(x_src_gpu)),
                    z_src_gpu,
                    bounds_error=False,
                    fill_value=float('nan')
                )
                pts = xp.column_stack([y_src_reproj.ravel(), x_src_reproj.ravel()])
                z_tgt = interp(cp.asnumpy(pts)).reshape(ny, nx)
            else:
                interp = RegularGridInterpolator(
                    (y_src_gpu, x_src_gpu),
                    z_src_gpu,
                    bounds_error=False,
                    fill_value=np.nan
                )
                pts = xp.column_stack([y_src_reproj.ravel(), x_src_reproj.ravel()])
                z_tgt = interp(pts).reshape(ny, nx)
            if ENABLE_TIMING:
                device_str = "GPU" if gpu_enabled else "CPU"
                logger.info(f"  [TIMING] reproject: RegularGridInterpolator ({device_str}, non-periodic): {(time.time() - t1)*1000:.2f}ms")

    else:
        # Curvilinear grid → need scattered interpolation
        # GPU doesn't support LinearNDInterpolator well, so fall back to CPU
        t1 = time.time() if ENABLE_TIMING else None
        if gpu_enabled:
            logger.warning("GPU acceleration not supported for curvilinear grids, falling back to CPU for interpolation")
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

        interp = LinearNDInterpolator(
            np.column_stack([x_src_cpu.flatten(), y_src_cpu.flatten()]),
            z_src_cpu.flatten(),
            fill_value=np.nan
        )
        pts = np.column_stack([x_src_reproj_cpu.ravel(), y_src_reproj_cpu.ravel()])
        z_tgt_cpu = interp(pts).reshape(ny, nx)

        # Convert back to GPU if needed
        z_tgt = cp.asarray(z_tgt_cpu) if gpu_enabled else z_tgt_cpu
        if ENABLE_TIMING:
            logger.info(f"  [TIMING] reproject: LinearNDInterpolator (curvilinear, CPU): {(time.time() - t1)*1000:.2f}ms")

    if ENABLE_TIMING:
        logger.info(f"  [TIMING] reproject: TOTAL interpolation: {(time.time() - t0)*1000:.2f}ms")

    # Convert GPU arrays back to CPU for return
    if gpu_enabled:
        t0 = time.time() if ENABLE_TIMING else None
        x_tgt = cp.asnumpy(x_tgt)
        y_tgt = cp.asnumpy(y_tgt)
        z_tgt = cp.asnumpy(z_tgt)
        if ENABLE_TIMING:
            logger.info(f"  [TIMING] reproject: GPU→CPU transfer: {(time.time() - t0)*1000:.2f}ms")

    if ENABLE_TIMING:
        logger.info(f"  [TIMING] reproject: === TOTAL reproject_to_grid: {(time.time() - t_start)*1000:.2f}ms ===")

    return x_tgt, y_tgt, z_tgt
