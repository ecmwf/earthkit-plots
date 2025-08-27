# Copyright 2024-, European Centre for Medium Range Weather Forecasts.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
import warnings

# import cartopy.crs as ccrs
import numpy as np

# earthkit.geo is not yet used
# TODO: Is this the best way to check for earthkit.geo?
# _NO_EARTHKIT_GEO = importlib.util.find_spec("earthkit.geo") is None


def is_structured(x, y, tol=1e-5, lon_wrap=True):
    """
    Determines whether the x and y points form a structured grid, accounting for longitude wrapping.

    Parameters
    ----------
    x : array_like
        A 1D or 2D array of x-coordinates (e.g., longitude or x in Cartesian grid).
    y : array_like
        A 1D or 2D array of y-coordinates (e.g., latitude or y in Cartesian grid).
    tol : float, optional
        Tolerance for floating-point comparison to account for numerical precision errors.
        Default is 1e-5.
    lon_wrap : bool, optional
        If True, handles cases where longitudes wrap around at -180/180 or 0/360.
        Default is True.

    Returns
    -------
    bool
        True if the data represents a structured grid, False otherwise.
    """
    x = np.asarray(x)
    y = np.asarray(y)

    def wrap_diff(arr):
        """Compute differences, considering longitude wrapping."""
        diff = np.diff(arr)
        if lon_wrap:
            diff = np.mod(diff + 180, 360) - 180  # Wrap differences to [-180, 180]
        return diff

    if x.ndim == 1 and y.ndim == 1:
        if len(x) * len(y) != x.size * y.size:
            return False

        x_diff = wrap_diff(x)
        y_diff = wrap_diff(y)

        x_spacing_consistent = np.all(np.abs(x_diff - x_diff[0]) < tol)
        y_spacing_consistent = np.all(np.abs(y_diff - y_diff[0]) < tol)

        return x_spacing_consistent and y_spacing_consistent

    elif x.ndim == 2 and y.ndim == 2:
        x_diff_rows = wrap_diff(x)
        y_diff_cols = wrap_diff(y)

        x_rows_consistent = np.all(np.abs(np.diff(x_diff_rows, axis=1)) < tol)
        y_columns_consistent = np.all(np.abs(np.diff(y_diff_cols, axis=0)) < tol)

        return x_rows_consistent and y_columns_consistent

    # Invalid input, dimensions of x and y must match (either both 1D or both 2D)
    return False


def is_global(x, y, tol=5):
    """
    Determines whether the x and y points form a global grid.

    Compares points of x and y to low resolution global grid,
    and if within tolerance, returns True.
    """
    # earthkit.geo is not yet used
    # TODO: Is this the best way to check for earthkit.geo? Can we copy what is done with scipy?
    # if not _NO_EARTHKIT_GEO:
    #     pass
    try:
        from scipy.spatial import KDTree
    except ImportError:
        raise ImportError(
            "The 'scipy' package is required for checking for global data."
        )

    expected_x = np.arange(0, 360, 2).reshape(-1, 1)
    expected_y = np.arange(-90, 90, 2).reshape(-1, 1)

    if np.any(x < 0):
        x = np.roll(x, -180)

    x_tree = KDTree(x.flatten().reshape(-1, 1))
    y_tree = KDTree(y.flatten().reshape(-1, 1))

    x_dist, _ = x_tree.query(expected_x)
    if np.any(x_dist > tol):
        return False

    y_dist, _ = y_tree.query(expected_y)
    if np.any(y_dist > tol):
        return False

    return True


def _guess_resolution_and_shape(
    x: np.ndarray,
    y: np.ndarray,
    in_shape: int | tuple[int, int] | None = None,
    in_resolution: float | tuple[float, float] | None = None,
) -> tuple[tuple[float, float], tuple[int, int]]:
    """
    Guess the resolution and shape of the grid based on the input data.
    """
    x_min, x_max = x.min(), x.max()
    y_min, y_max = y.min(), y.max()

    # If a target resolution provided, calculate the target shape from the resolution and the x/y values
    if in_resolution is not None:
        # Determine shape from in_resolution
        if not isinstance(in_resolution, (tuple, list)):
            out_resolution: tuple[float, float] = (in_resolution, in_resolution)
        else:
            out_resolution = in_resolution
        if in_shape is not None:
            warnings.warn(
                "Both shape and resolution are provided, using resolution to determine shape."
            )
        out_shape = (
            int((x_max - x_min) / out_resolution[0]) + 1,
            int((y_max - y_min) / out_resolution[1]) + 1,
        )
        return out_resolution, out_shape

    # If a target shape provided, calculate the target resolution from the shape and the x/y values
    if in_shape is not None:
        # Determine resolution from in_shape
        if not isinstance(in_shape, (tuple, list)):
            out_shape: tuple[int, int] = (in_shape, in_shape)
        else:
            out_shape = in_shape
        out_resolution = (
            float(x_max - x_min) / out_shape[0],
            float(y_max - y_min) / out_shape[1],
        )
        return out_resolution, out_shape

    # If neither are defined, guess the resolution from the data and calculate the shape

    try:
        from scipy.spatial import cKDTree
    except ImportError:
        raise ImportError(
            "The 'scipy.spatial' module is required for guessing resolution and shape."
            "Alternatively, provide a target resolution or shape."
        )
    # Use cKDTree to find nearest distances
    points = np.c_[x, y]
    tree = cKDTree(points)
    distances, _ = tree.query(points, k=2)

    # Use the median of the distances as the resolution,
    # ensuring any duplicated points are ignored, this is cheaper than filtering points
    _resolution = np.median(distances[distances > 0])
    out_resolution = (_resolution, _resolution)

    out_shape = (
        int((x_max - x_min) / out_resolution[0]) + 1,
        int((y_max - y_min) / out_resolution[1]) + 1,
    )
    return out_resolution, out_shape


def interpolate_unstructured(
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray,
    target_shape: tuple[int, int] | int | None = None,
    target_resolution: tuple[float, float] | float | None = None,
    method: str = "linear",
    distance_threshold: None | float | int | str = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Interpolate unstructured data to a structured grid.

    This function takes unstructured (scattered) data points and interpolates them
    to a structured grid, handling NaN values in `z` and providing options for
    different interpolation methods. It creates a regular grid based on the given
    number of cells (n_cells) and interpolates the z-values from the unstructured points onto this grid.

    Parameters
    ----------
    x : array_like
        1D array of x-coordinates.
    y : array_like
        1D array of y-coordinates.
    z : array_like
        1D array of z-values at each (x, y) point.
    target_shape : tuple(int), optional
        The number of points along x and y axes for the structured grid, it should be provided as
        (n_cells_x, n_cells_y). If None, the number of points is determined based on the
        resolution of the data.
        Default is None.
    target_resolution : float, optional
        The resolution of the plot grid in the same units as the x and y coordinates.
        It can be provided as a single float or a tuple of two floats (resolution_x, resolution_y).
        If None, the resolution is guessed based on the minimum distance between points.
        Default is None.
    method : {'linear', 'nearest', 'cubic'}, optional
        The interpolation method to use. Default is 'linear'.
        The methods supported are:

        - 'linear': Linear interpolation between points.
        - 'nearest': Nearest-neighbor interpolation.
        - 'cubic': Cubic interpolation, which may produce smoother results.
    distance_threshold: None | int | float | str, optional
        A cell will only be plotted if there is at least one data point within this distance (inclusive).
        If None, all points are plotted. If an integer or float, the distance is
        in the units of the plot projection (e.g. degrees for `ccrs.PlateCarree`).
        If 'auto', the distance is automatically determined based on the plot resolution.
        If a string that ends with 'cells' (e.g. '2 cells') the distance threshold is
        that number of cells on the plot grid.
        Default is None.

    Returns
    -------
    grid_x : ndarray
        2D array representing the x-coordinates of the structured grid.
    grid_y : ndarray
        2D array representing the y-coordinates of the structured grid.
    grid_z : ndarray
        2D array of interpolated z-values at the grid points. NaNs may be
        present in regions where interpolation was not possible (e.g., due to
        large gaps in the data).
    """
    try:
        from scipy.interpolate import griddata
    except ImportError:
        raise ImportError(
            "The 'scipy' package is required for interpolating unstructured data."
        )

    target_resolution, target_shape = _guess_resolution_and_shape(
        x, y, in_shape=target_shape, in_resolution=target_resolution
    )

    # Create a structured grid
    grid_x, grid_y = np.mgrid[
        x.min() : x.max() : target_shape[0] * 1j,
        y.min() : y.max() : target_shape[1] * 1j,
    ]

    # Filter out NaN values from z and corresponding x, y
    mask = ~np.isnan(z)
    x_filtered = x[mask]
    y_filtered = y[mask]
    z_filtered = z[mask]

    # Interpolate the filtered data onto the structured grid
    grid_z = griddata(
        np.column_stack((x_filtered, y_filtered)),
        z_filtered,
        (grid_x, grid_y),
        method=method,
    )

    if np.isnan(grid_z).any() and is_global(x, y, np.max(np.diff(np.unique(y))) * 2):
        warnings.warn(
            "Interpolation produced NaN values in the global output grid, reinterpolating with `nearest`."
        )
        return interpolate_unstructured(
            x,
            y,
            z,
            target_resolution=target_resolution,
            method="nearest",
            distance_threshold=distance_threshold,
        )

    if distance_threshold is None:
        return grid_x, grid_y, grid_z

    try:
        from scipy.spatial import cKDTree
    except ImportError:
        raise ImportError(
            "The 'scipy.spatial' module is required for applying a distance threshold."
        )
    # Use cKDTree to find nearest distances
    tree = cKDTree(np.c_[x_filtered, y_filtered])
    grid_points = np.c_[grid_x.ravel(), grid_y.ravel()]
    distances, _ = tree.query(grid_points)

    value_error_message = (
        "Invalid value for 'distance_threshold'. "
        "Expected an integer, a float, a string 'auto', or a string in the format 'N cells'."
    )
    try:
        distance_threshold = float(distance_threshold)
    except ValueError:
        # ensure string provided is lower case and without spaces
        distance_threshold = str(distance_threshold).lower().replace(" ", "")
        # use the mean resolution of the plotting grid
        plot_resolution = max(target_resolution[0], target_resolution[1])
        if distance_threshold == "auto":
            # data_resolution = max(guess_resolution(x_filtered), guess_resolution(y_filtered))
            distance_threshold = plot_resolution * 2.0
            # Some hard-coded values, but this is auto-mode, so not for user configurability
        elif distance_threshold.endswith("cells"):
            match = re.match(r"(\d+\.?\d*)cells", distance_threshold)
            if match is None:
                raise ValueError(value_error_message)
            _n_cells = float(match.group(1))
            distance_threshold = _n_cells * plot_resolution
        else:
            raise ValueError(value_error_message)

    # Mask points where the nearest data point is beyond the threshold
    grid_z = np.where(
        distances.reshape(grid_x.shape) <= distance_threshold,
        grid_z,
        np.nan,
    )

    return grid_x, grid_y, grid_z


def needs_cyclic_point(lons):
    return is_global(lons, np.arange(-90, 90, 2)) and is_structured(
        lons, np.arange(-90, 90, 2)
    )

    lons = np.asarray(lons)
    lons_sorted = np.sort(lons)
    delta = np.median(np.diff(lons_sorted))  # Robust estimate of the longitude step

    actual_min, actual_max = np.min(lons), np.max(lons)

    # Define both possible expected ranges
    expected_range_360 = [0, 360]
    expected_range_180 = [-180, 180]

    # Define the tolerances for each range taking into account the step size
    tolerance = delta / 2  # Adjust tolerance as a fraction of the longitude step

    # Check if the actual range covers the expected range within tolerance
    check_360 = np.isclose(
        actual_min, expected_range_360[0], atol=tolerance
    ) and np.isclose(actual_max, expected_range_360[1] - delta, atol=tolerance)
    check_180 = np.isclose(
        actual_min, expected_range_180[0], atol=tolerance
    ) and np.isclose(actual_max, expected_range_180[1] - delta, atol=tolerance)

    return check_360 or check_180
