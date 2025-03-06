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

import numpy as np

_NO_SCIPY = False
try:
    from scipy.interpolate import griddata
except ImportError:
    _NO_SCIPY = True


def is_structured(x, y, tol=1e-5):
    """
    Determines whether the x and y points form a structured grid.

    This function checks if the x and y coordinate arrays represent a structured
    grid, i.e., a grid with consistent spacing between points. The function supports
    1D arrays (representing coordinates of a grid) and 2D arrays (representing the
    actual grid coordinates) of x and y.

    Parameters
    ----------
    x : array_like
        A 1D or 2D array of x-coordinates. For example, this can be longitude or
        the x-coordinate in a Cartesian grid.
    y : array_like
        A 1D or 2D array of y-coordinates. For example, this can be latitude or
        the y-coordinate in a Cartesian grid.
    tol : float, optional
        Tolerance for floating-point comparison to account for numerical precision
        errors when checking spacing consistency. The default is 1e-5.

    Returns
    -------
    bool
        True if the data represents a structured grid, i.e., the spacing between
        consecutive points in both x and y is consistent. False otherwise.
    """

    x = np.asarray(x)
    y = np.asarray(y)

    # If both x and y are 1D arrays, ensure they can form a grid
    if x.ndim == 1 and y.ndim == 1:
        # Check if the number of points match (can form a meshgrid)
        if len(x) * len(y) != x.size * y.size:
            return False

        # Check consistent spacing in x and y
        x_diff = np.diff(x)
        y_diff = np.diff(y)

        x_spacing_consistent = np.all(np.abs(x_diff - x_diff[0]) < tol)
        y_spacing_consistent = np.all(np.abs(y_diff - y_diff[0]) < tol)

        return x_spacing_consistent and y_spacing_consistent

    # If x and y are 2D arrays, verify they are structured as a grid
    elif x.ndim == 2 and y.ndim == 2:
        # Check if rows of x and y have consistent spacing along the grid lines
        # x should vary only along one axis, y along the other axis

        x_rows_consistent = np.all(
            np.abs(np.diff(x, axis=1) - np.diff(x, axis=1)[:, 0:1]) < tol
        )
        y_columns_consistent = np.all(
            np.abs(np.diff(y, axis=0) - np.diff(y, axis=0)[0:1, :]) < tol
        )

        return x_rows_consistent and y_columns_consistent

    else:
        # Invalid input, dimensions of x and y must match (either both 1D or both 2D)
        return False


def interpolate_unstructured(
    x, y, z, resolution=1000, method="linear",
    interpolation_distance_threshold: None | float | int | str = None,
):
    """
    Interpolate unstructured data to a structured grid.

    This function takes unstructured (scattered) data points and interpolates them
    to a structured grid, handling NaN values in `z` and providing options for
    different interpolation methods. It creates a regular grid based on the given
    resolution and interpolates the z-values from the unstructured points onto this grid.

    Parameters
    ----------
    x : array_like
        1D array of x-coordinates.
    y : array_like
        1D array of y-coordinates.
    z : array_like
        1D array of z-values at each (x, y) point.
    resolution : int, optional
        The number of points along each axis for the structured grid.
        Default is 1000.
    method : {'linear', 'nearest', 'cubic'}, optional
        The interpolation method to use. Default is 'linear'.
        The methods supported are:

        - 'linear': Linear interpolation between points.
        - 'nearest': Nearest-neighbor interpolation.
        - 'cubic': Cubic interpolation, which may produce smoother results.
    interpolation_distance_threshold: None | int | float | str, optional
        A cell will only be plotted if there is at least one data point within this distance.
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
    if _NO_SCIPY:
        raise ImportError(
            "The 'scipy' package is required for interpolating unstructured data."
        )
    # Filter out NaN values from z and corresponding x, y
    mask = ~np.isnan(z)
    x_filtered = x[mask]
    y_filtered = y[mask]
    z_filtered = z[mask]

    # Create a structured grid
    grid_x, grid_y = np.mgrid[
        x.min() : x.max() : resolution * 1j, y.min() : y.max() : resolution * 1j
    ]

    # Interpolate the filtered data onto the structured grid
    grid_z = griddata(
        np.column_stack((x_filtered, y_filtered)),
        z_filtered,
        (grid_x, grid_y),
        method=method,
    )

    if interpolation_distance_threshold is not None:
        
        if isinstance(interpolation_distance_threshold, str):
            try:
                interpolation_distance_threshold = float(interpolation_distance_threshold)
            except ValueError:
                if interpolation_distance_threshold == 'auto':
                    npoints = 3
                elif interpolation_distance_threshold.endswith('cells'):
                    npoints = int(interpolation_distance_threshold[:-5].strip(' '))
                else:
                    raise ValueError(
                        "Invalid value for 'interpolation_distance_threshold'. "
                        "Expected an integer or a string ending with 'cells' or 'auto'."
                    )
                # Calculate the resolution of the grid
                res = (
                    ((x.max() - x.min()) / resolution)**2 + 
                    ((y.max() - y.min()) / resolution)**2
                )**0.5
                interpolation_distance_threshold = npoints*res
        from scipy.spatial import cKDTree
        # Use cKDTree to find nearest distances
        tree = cKDTree(np.c_[x_filtered, y_filtered])
        grid_points = np.c_[grid_x.ravel(), grid_y.ravel()]
        distances, _ = tree.query(grid_points)

        # Mask points where the nearest source is beyond the threshold
        grid_z = np.where(distances.reshape(grid_x.shape) <= interpolation_distance_threshold, grid_z, np.nan)

    return grid_x, grid_y, grid_z


def needs_cyclic_point(lons):
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
