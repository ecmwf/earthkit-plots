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
from scipy.interpolate import griddata


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
  

def interpolate_unstructured(x, y, z, resolution=100, method="bilinear"):
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
    # Filter out NaN values from z and corresponding x, y
    mask = ~np.isnan(z)
    x_filtered = x[mask]
    y_filtered = y[mask]
    z_filtered = z[mask]
    
    # Create a structured grid
    grid_x, grid_y = np.mgrid[x.min():x.max():resolution*1j, y.min():y.max():resolution*1j]
    
    # Interpolate the filtered data onto the structured grid
    grid_z = griddata(np.column_stack((x_filtered, y_filtered)), z_filtered, (grid_x, grid_y), method=method)
    
    return grid_x, grid_y, grid_z

import numpy as np
from scipy.interpolate import griddata
import alphashape
from shapely.geometry import Point

def interpolate_unstructured(x, y, z, resolution=300, method="cubic", alpha=4):
    """
    Interpolates unstructured data to a structured grid, handling NaNs in z-values
    and preventing interpolation outside a concave hull (alpha shape) of the point cloud.
    
    Parameters:
    - x: 1D array of x-coordinates.
    - y: 1D array of y-coordinates.
    - z: 1D array of z values.
    - resolution: The number of points along each axis for the structured grid.
    - method: Interpolation method ('linear', 'nearest', 'cubic').
    - alpha: The alpha parameter for controlling the concavity of the alpha shape (concave hull).
    
    Returns:
    - grid_x: 2D grid of x-coordinates.
    - grid_y: 2D grid of y-coordinates.
    - grid_z: 2D grid of interpolated z-values, masked outside the concave hull.
    """
    # Filter out NaN values from z and corresponding x, y
    mask = ~np.isnan(z)
    x_filtered = x[mask]
    y_filtered = y[mask]
    z_filtered = z[mask]

    # Create a structured grid
    grid_x, grid_y = np.mgrid[x.min():x.max():resolution*1j, y.min():y.max():resolution*1j]
    
    # Interpolate the filtered data onto the structured grid
    grid_z = griddata(np.column_stack((x_filtered, y_filtered)), z_filtered, (grid_x, grid_y), method=method)

    # Compute the alpha shape (concave hull) of the points
    points = np.column_stack((x_filtered, y_filtered))
    alpha_shape = alphashape.alphashape(points, alpha)

    # Create a mask to determine if the grid points are inside the alpha shape
    grid_points = np.column_stack([grid_x.flatten(), grid_y.flatten()])
    mask = np.array([alpha_shape.contains(Point(p)) for p in grid_points])

    # Apply the mask to the interpolated grid
    grid_z = grid_z.flatten()
    grid_z[~mask] = np.nan  # Set values outside the alpha shape to NaN
    grid_z = grid_z.reshape(grid_x.shape)
    
    return grid_x, grid_y, grid_z
