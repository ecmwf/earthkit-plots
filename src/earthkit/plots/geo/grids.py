# Copyright 2024, European Centre for Medium Range Weather Forecasts.
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


def is_structured(lat, lon, tol=1e-5):
    """
    Determines whether the latitude and longitude points form a structured grid.

    Parameters:
    - lat: A 1D or 2D array of latitude points.
    - lon: A 1D or 2D array of longitude points.
    - tol: Tolerance for floating-point comparison (default 1e-5).

    Returns:
    - True if the data is structured (grid), False if it's unstructured.
    """

    lat = np.asarray(lat)
    lon = np.asarray(lon)

    # Check if there are consistent spacing in latitudes and longitudes
    unique_lat = np.unique(lat)
    unique_lon = np.unique(lon)

    # Structured grid condition: the number of unique lat/lon values should multiply to the number of total points
    if len(unique_lat) * len(unique_lon) == len(lat) * len(lon):
        # Now check if the spacing is consistent
        lat_diff = np.diff(unique_lat)
        lon_diff = np.diff(unique_lon)

        # Check if lat/lon differences are consistent
        lat_spacing_consistent = np.all(np.abs(lat_diff - lat_diff[0]) < tol)
        lon_spacing_consistent = np.all(np.abs(lon_diff - lon_diff[0]) < tol)

        return lat_spacing_consistent and lon_spacing_consistent

    # If the product of unique lat/lon values doesn't match total points, it's unstructured
    return False


def interpolate_unstructured(x, y, z, resolution=1000, method="linear"):
    """
    Interpolates unstructured data to a structured grid, handling NaNs in z-values
    and preventing interpolation across large gaps.

    Parameters:
    - x: 1D array of x-coordinates.
    - y: 1D array of y-coordinates.
    - z: 1D array of z values.
    - resolution: The number of points along each axis for the structured grid.
    - method: Interpolation method ('linear', 'nearest', 'cubic').
    - gap_threshold: The distance threshold beyond which interpolation is not performed (set to NaN).

    Returns:
    - grid_x: 2D grid of x-coordinates.
    - grid_y: 2D grid of y-coordinates.
    - grid_z: 2D grid of interpolated z-values, with NaNs in large gap regions.
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

    return grid_x, grid_y, grid_z
