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

"""Shared pytest fixtures for sources tests."""

import numpy as np
import pytest
import xarray as xr


@pytest.fixture
def simple_1d_array():
    """Simple 1D numpy array."""
    return np.array([1, 2, 3, 4, 5])


@pytest.fixture
def simple_2d_array():
    """Simple 2D numpy array."""
    return np.array([[1, 2, 3], [4, 5, 6]])


@pytest.fixture
def grid_2d_arrays():
    """2D data with 1D coordinate arrays for map plotting."""
    data = np.random.rand(15, 30)
    y = np.linspace(-90, 90, 15)
    x = np.linspace(-180, 180, 30)
    return data, x, y


@pytest.fixture
def simple_xarray_2d():
    """Simple 2D xarray DataArray with lat/lon."""
    return xr.DataArray(
        np.array([[1, 2, 3], [4, 5, 6]]),
        dims=["latitude", "longitude"],
        coords={"latitude": [10, 20], "longitude": [100, 110, 120]},
    )


@pytest.fixture
def xarray_with_units():
    """Xarray DataArray with units in attrs."""
    return xr.DataArray(
        np.array([273.15, 283.15, 293.15]),
        dims=["time"],
        coords={"time": [0, 1, 2]},
        attrs={"units": "K", "long_name": "Temperature"},
    )


@pytest.fixture
def xarray_dataset_single_var():
    """Xarray Dataset with single variable."""
    return xr.Dataset(
        {
            "temperature": (["latitude", "longitude"], [[1, 2, 3], [4, 5, 6]]),
        },
        coords={"latitude": [10, 20], "longitude": [100, 110, 120]},
    )


@pytest.fixture
def xarray_with_projection():
    """Xarray with Lambert Conformal projection metadata."""
    projection = xr.DataArray(
        0,
        attrs={
            "grid_mapping_name": "lambert_conformal_conic",
            "standard_parallel": [25.0, 35.0],
            "longitude_of_central_meridian": -95.0,
            "latitude_of_projection_origin": 15.0,
        },
    )

    data = xr.DataArray(
        [[1, 2], [3, 4]],
        dims=["y", "x"],
        coords={
            "x": ("x", [100000, 200000]),
            "y": ("y", [300000, 400000]),
        },
        attrs={"grid_mapping": "lambert_conformal_conic"},
    )

    return xr.Dataset({"temperature": data, "lambert_conformal_conic": projection})
