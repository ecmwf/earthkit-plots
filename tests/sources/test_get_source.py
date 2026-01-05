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

"""Tests for the get_source factory function."""

import numpy as np
import xarray as xr

from earthkit.plots.sources import Source, get_source
from earthkit.plots.sources.context import PlotContext


def test_get_source_returns_source():
    """Test that get_source returns a Source instance."""
    source = get_source(np.array([1, 2, 3]), context=PlotContext.CARTESIAN_1D)
    assert isinstance(source, Source)


def test_get_source_numpy_array():
    """Test that get_source handles numpy arrays with NumpyExtractor."""
    source = get_source(np.array([1, 2, 3]), context=PlotContext.CARTESIAN_1D)
    assert source._extractor.__class__.__name__ == "NumpyExtractor"
    assert np.array_equal(source.y.values, np.array([1, 2, 3]))


def test_get_source_xarray_dataarray():
    """Test that get_source handles xarray DataArray with XarrayExtractor."""
    da = xr.DataArray([1, 2, 3], dims=["time"], coords={"time": [0, 1, 2]})
    source = get_source(da)
    assert source._extractor.__class__.__name__ == "XarrayExtractor"


def test_get_source_xarray_dataset():
    """Test that get_source handles xarray Dataset with XarrayExtractor."""
    ds = xr.Dataset(
        {"temperature": (["time"], [1, 2, 3])},
        coords={"time": [0, 1, 2]},
    )
    source = get_source(ds)
    assert source._extractor.__class__.__name__ == "XarrayExtractor"


def test_get_source_with_context():
    """Test that get_source accepts PlotContext parameter."""
    source = get_source(
        np.array([1, 2, 3]),
        context=PlotContext.CARTESIAN_1D,
    )
    assert isinstance(source, Source)


def test_get_source_with_coordinates():
    """Test that get_source accepts x, y, z parameters."""
    data = np.array([[1, 2, 3], [4, 5, 6]])
    x = np.array([10, 20, 30])
    y = np.array([100, 200])

    source = get_source(data, x=x, y=y, context=PlotContext.CARTESIAN_2D)

    # Should create meshgrid from 1D coords
    assert source.x.values.shape == (2, 3)
    assert source.y.values.shape == (2, 3)
    assert source.z.values.shape == (2, 3)


def test_get_source_with_metadata():
    """Test that get_source accepts metadata parameter."""
    source = get_source(
        np.array([1, 2, 3]),
        metadata={"units": "meters", "long_name": "Distance"},
    )
    assert source.metadata("units") == "meters"
    assert source.metadata("long_name") == "Distance"


def test_get_source_with_units_conversion():
    """Test that get_source accepts units parameter for conversion."""
    da = xr.DataArray(
        [273.15, 283.15, 293.15],
        attrs={"units": "K"},
    )
    source = get_source(da, units="degC", context=PlotContext.CARTESIAN_1D)

    # Values should be converted from K to °C
    expected = np.array([0.0, 10.0, 20.0])
    assert np.allclose(source.y.values, expected)


def test_get_source_default_context():
    """Test that get_source uses CARTESIAN_2D as default context."""
    data = np.array([[1, 2, 3], [4, 5, 6]])
    source = get_source(data)
    # Default context should be CARTESIAN_2D for 2D data
    assert source.z is not None
    assert source.z.values.shape == (2, 3)
