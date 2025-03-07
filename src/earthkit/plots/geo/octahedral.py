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

import cartopy.crs as ccrs
import numpy as np


def plot_octahedral_grid(lons, lats, data, ax, style=None, **kwargs):
    """
    Plot an octahedral reduced Gaussian grid using PolyCollection with given assumptions.

    Args:
        lats (array): 1D array of latitudes.
        lons (array): 1D array of longitudes.
        data (1D array): 1D data array.
    """
    import matplotlib.collections as mcoll

    # Convert longitudes from [0, 360] to [-180, 180]
    lons = np.where(lons > 180, lons - 360, lons)

    # Calculate d_lat as the average of differences between unique sorted latitudes
    unique_lats = np.unique(lats)
    # d_lat = np.mean(np.diff(unique_lats))
    d_lats = calculate_row_heights(unique_lats)
    # d_lat = d_lats[0]

    # Prepare vertices for each polygon
    polygons = []
    color_data = []
    current_lat = lats[0]
    i_lat = 0
    for i in range(len(data)):
        d_lat = d_lats[i_lat]
        if i > 0 and lats[i] != current_lat:
            # We are in a new row, recalculate d_lon
            d_lon = (
                lons[i + 1] - lons[i]
            )  # Assuming that the next point is in the new row
            current_lat = lats[i]
            i_lat += 1
        elif i == 0:
            d_lon = lons[i + 1] - lons[i]

        lon = lons[i]
        lat = lats[i]
        # Define the four corners of each cell, ensuring 5% overlap by reducing edge effect
        lat_pad = d_lat / 20
        lon_pad = d_lon / 20
        polygons.append(
            [
                [lon - d_lon / 2 - lon_pad, lat - d_lat / 2 - lat_pad],
                [lon + d_lon / 2 + lon_pad, lat - d_lat / 2 - lat_pad],
                [lon + d_lon / 2 + lon_pad, lat + d_lat / 2 + lat_pad],
                [lon - d_lon / 2 - lon_pad, lat + d_lat / 2 + lat_pad],
            ]
        )
        color_data.append(data[i])

    if style is not None:
        kwargs = {
            **kwargs,
            **style.to_pcolormesh_kwargs(data),
            **{"transform": ccrs.PlateCarree()},
        }

    # Create a PolyCollection with slight overlap to prevent gaps
    poly_collection = mcoll.PolyCollection(
        polygons, array=np.array(color_data), edgecolors="none", **kwargs
    )

    ax.add_collection(poly_collection)

    return poly_collection


def calculate_row_heights(lats):
    """
    Calculate the heights of latitude rows such that each latitude
    value lies in the center of its row, with row boundaries equidistant
    between consecutive latitudes.

    Parameters:
        lats (array-like): An array of latitude values.

    Returns:
        numpy.ndarray: An array containing the heights of each row.
    """
    # Ensure input is a numpy array and sort it
    lats = np.sort(np.array(lats))

    # Calculate mid-points between consecutive latitudes
    mid_points = (lats[:-1] + lats[1:]) / 2

    # Calculate the first and last boundaries by extrapolation
    first_boundary = 2 * lats[0] - mid_points[0]
    last_boundary = 2 * lats[-1] - mid_points[-1]

    # Create the complete list of boundaries
    boundaries = np.concatenate(([first_boundary], mid_points, [last_boundary]))

    # Calculate and return the heights of each row
    return np.diff(boundaries)
