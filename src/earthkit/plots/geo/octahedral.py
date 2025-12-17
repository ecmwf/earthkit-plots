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


class ReducedGaussianGrid:
    """
    Fast lookup structure for reduced Gaussian grid data.

    This class builds an efficient index for mapping lat/lon coordinates
    to grid cell values, similar to healpy's ang2pix for HEALPix grids.
    """

    def __init__(self, lons, lats, values):
        """
        Initialize the reduced Gaussian grid lookup structure.

        Parameters
        ----------
        lons : array-like
            Longitude values of grid points
        lats : array-like
            Latitude values of grid points
        values : array-like
            Data values at grid points
        """
        # Convert to numpy arrays and normalize longitudes to [-180, 180]
        self.lons = np.asarray(lons)
        self.lats = np.asarray(lats)
        self.values = np.asarray(values)

        self.lons = np.where(self.lons > 180, self.lons - 360, self.lons)

        # Find unique latitudes and sort north to south
        unique_lats = np.unique(self.lats)
        self.unique_lats = np.sort(unique_lats)[::-1]

        # Build lookup structure for each latitude band
        self.lat_bands = []
        for lat in self.unique_lats:
            mask = np.abs(self.lats - lat) < 1e-6
            band_lons = self.lons[mask]
            band_vals = self.values[mask]

            # Sort by longitude
            sort_idx = np.argsort(band_lons)
            band_lons = band_lons[sort_idx]
            band_vals = band_vals[sort_idx]

            self.lat_bands.append({
                'lons': band_lons,
                'values': band_vals,
                'n_points': len(band_lons),
                'dlon': 360.0 / len(band_lons)
            })

        # Calculate latitude boundaries (midpoints between consecutive lats)
        self.lat_bounds = np.zeros(len(self.unique_lats) + 1)
        for i in range(len(self.unique_lats) - 1):
            self.lat_bounds[i + 1] = (self.unique_lats[i] + self.unique_lats[i + 1]) / 2
        self.lat_bounds[0] = self.unique_lats[0] + (self.unique_lats[0] - self.lat_bounds[1])
        self.lat_bounds[-1] = self.unique_lats[-1] - (self.lat_bounds[-2] - self.unique_lats[-1])
        self.lat_bounds = np.clip(self.lat_bounds, -90, 90)

    def get_value(self, lat, lon):
        """
        Get the grid value at a given lat/lon coordinate.

        Parameters
        ----------
        lat : float or array-like
            Latitude(s) in degrees
        lon : float or array-like
            Longitude(s) in degrees

        Returns
        -------
        value : float or array
            Grid value(s) at the given coordinate(s), NaN if outside grid
        """
        # Handle scalar vs array input
        scalar_input = np.isscalar(lat)
        lat = np.atleast_1d(lat)
        lon = np.atleast_1d(lon)

        # Normalize longitudes to [-180, 180]
        lon = np.where(lon > 180, lon - 360, lon)

        # Initialize result
        result = np.full(len(lat), np.nan, dtype=self.values.dtype)

        # Use np.searchsorted to find which latitude band each point belongs to
        # lat_bounds is sorted in descending order, so we need to reverse
        lat_band_indices = np.searchsorted(self.lat_bounds[::-1], lat, side='left')
        lat_band_indices = len(self.lat_bounds) - 1 - lat_band_indices

        # For each latitude band, vectorize the lookup
        for i, band in enumerate(self.lat_bands):
            # Find query points in this latitude band using the precomputed indices
            in_band = (lat_band_indices == i)
            if not np.any(in_band):
                continue

            band_lons = band['lons']
            band_vals = band['values']
            dlon = band['dlon']

            # Get query longitudes in this band
            q_lons = lon[in_band]

            # For grids with many points per band, use searchsorted for faster lookup
            # For smaller bands, broadcasting is fine
            if len(band_lons) > 100:
                # Use searchsorted to find nearest neighbors more efficiently
                indices = np.searchsorted(band_lons, q_lons)

                # Check both the found index and the previous one
                indices = np.clip(indices, 0, len(band_lons) - 1)
                indices_prev = np.clip(indices - 1, 0, len(band_lons) - 1)

                # Calculate distances to both candidates
                dist_curr = np.abs(q_lons - band_lons[indices])
                dist_curr = np.minimum(dist_curr, 360 - dist_curr)

                dist_prev = np.abs(q_lons - band_lons[indices_prev])
                dist_prev = np.minimum(dist_prev, 360 - dist_prev)

                # Choose the closer one
                use_prev = dist_prev < dist_curr
                min_indices = np.where(use_prev, indices_prev, indices)
                min_dists = np.where(use_prev, dist_prev, dist_curr)
            else:
                # Original broadcasting approach for small bands
                dists = np.abs(q_lons[:, None] - band_lons[None, :])
                dists = np.minimum(dists, 360 - dists)
                min_indices = np.argmin(dists, axis=1)
                min_dists = dists[np.arange(len(q_lons)), min_indices]

            # Only assign values where distance is within dlon/2
            valid = min_dists < dlon / 2
            band_indices = np.where(in_band)[0]
            result[band_indices[valid]] = band_vals[min_indices[valid]]

        return result[0] if scalar_input else result


def nnshow(lons, lats, var, nx=1000, ny=1000, ax=None, style=None, **kwargs):
    """
    Plot reduced Gaussian/octahedral grid data using PolyCollection.

    This is a simple wrapper around plot_octahedral_grid for compatibility.
    The nx and ny parameters are ignored.
    """
    kwargs.pop("transform_first", None)
    return plot_octahedral_grid(lons, lats, var, ax, style=style, **kwargs)


def calculate_lat_boundaries(lats):
    """
    Calculate latitude boundaries such that each latitude value lies at the center of its cell.

    Parameters
    ----------
    lats : array-like
        Sorted array of latitude values (should be descending, North to South).

    Returns
    -------
    numpy.ndarray
        Array of latitude boundaries with length len(lats) + 1.
    """
    lats = np.asarray(lats)
    n = len(lats)
    bounds = np.zeros(n + 1)

    # Calculate midpoints between consecutive latitudes
    for i in range(n - 1):
        bounds[i + 1] = (lats[i] + lats[i + 1]) / 2

    # Extrapolate for first and last boundaries
    bounds[0] = lats[0] + (lats[0] - bounds[1])
    bounds[n] = lats[n - 1] - (bounds[n - 1] - lats[n - 1])

    # Clamp to valid latitude range
    bounds = np.clip(bounds, -90, 90)

    return bounds


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
