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

"""Tests for numpy array sources using the unified Source system."""

import numpy as np

from earthkit.plots.sources import get_source
from earthkit.plots.sources.context import PlotContext

# =============================================================================
# Basic Coordinate Extraction Tests
# =============================================================================


def test_numpy_1d_data_single_arg():
    """Test 1D data as single argument (interpreted as y-values)."""
    source = get_source([1, 2, 3], context=PlotContext.CARTESIAN_1D)
    assert np.array_equal(source.x.values, np.array([0, 1, 2]))
    assert np.array_equal(source.y.values, np.array([1, 2, 3]))
    assert source.z is None


def test_numpy_2d_data_single_arg():
    """Test 2D data as single argument (interpreted as z-values)."""
    source = get_source([[1, 2, 3], [4, 5, 6]], context=PlotContext.CARTESIAN_2D)
    # Should generate meshgrid for x and y
    assert source.x.values.shape == (2, 3)
    assert source.y.values.shape == (2, 3)
    assert np.array_equal(source.z.values, np.array([[1, 2, 3], [4, 5, 6]]))


def test_numpy_explicit_x_y():
    """Test explicit x and y arrays."""
    source = get_source(
        [1, 2, 3], x=[10, 20, 30], y=[1, 2, 3], context=PlotContext.CARTESIAN_1D
    )
    assert np.array_equal(source.x.values, np.array([10, 20, 30]))
    assert np.array_equal(source.y.values, np.array([1, 2, 3]))
    assert source.z is None


def test_numpy_explicit_x_y_z():
    """Test explicit x, y, and z arrays."""
    x = np.array([1, 2, 3])
    y = np.array([4, 5])
    z = np.array([[10, 20, 30], [40, 50, 60]])

    source = get_source(z, x=x, y=y, context=PlotContext.CARTESIAN_2D)

    # Should create meshgrid from 1D x and y
    assert source.x.values.shape == (2, 3)
    assert source.y.values.shape == (2, 3)
    assert np.array_equal(source.z.values, z)


# =============================================================================
# Meshgrid Creation Tests (NEW FEATURE)
# =============================================================================


def test_numpy_meshgrid_cartesian_2d():
    """Test automatic meshgrid creation for 2D cartesian plots."""
    data = np.random.rand(15, 30)
    y = np.linspace(0, 10, 15)
    x = np.linspace(0, 20, 30)

    source = get_source(data, x=x, y=y, context=PlotContext.CARTESIAN_2D)

    # Should create meshgrid
    assert source.x.values.shape == (15, 30)
    assert source.y.values.shape == (15, 30)
    assert source.z.values.shape == (15, 30)

    # Check meshgrid values
    assert np.array_equal(source.x.values[0, :], x)
    assert np.array_equal(source.y.values[:, 0], y)


def test_numpy_meshgrid_geographic_2d():
    """Test automatic meshgrid creation for geographic maps."""
    data = np.random.rand(15, 30)
    y = np.linspace(-90, 90, 15)  # latitude
    x = np.linspace(-180, 180, 30)  # longitude

    source = get_source(data, x=x, y=y, context=PlotContext.GEOGRAPHIC_2D)

    # Should create meshgrid
    assert source.x.values.shape == (15, 30)
    assert source.y.values.shape == (15, 30)
    assert source.z.values.shape == (15, 30)


def test_numpy_no_meshgrid_for_2d_coords():
    """Test that meshgrid is not applied when coords are already 2D."""
    x_2d = np.array([[1, 2, 3], [1, 2, 3]])
    y_2d = np.array([[1, 1, 1], [2, 2, 2]])
    z = np.array([[10, 20, 30], [40, 50, 60]])

    source = get_source(z, x=x_2d, y=y_2d, context=PlotContext.CARTESIAN_2D)

    # Should use 2D arrays as-is
    assert np.array_equal(source.x.values, x_2d)
    assert np.array_equal(source.y.values, y_2d)
    assert np.array_equal(source.z.values, z)


def test_numpy_scattered_points_1d():
    """Test scattered point data with 1D x, y, z arrays in 2D context."""
    # Scattered points: each (x[i], y[i], z[i]) is a single point
    x = np.array([1.5, 2.3, 4.1, 5.7, 3.2])
    y = np.array([2.1, 4.5, 1.8, 3.9, 5.0])
    z = np.array([10, 20, 15, 25, 18])

    source = get_source(z, x=x, y=y, context=PlotContext.CARTESIAN_2D)

    # Should keep as 1D - no meshgrid for scattered points
    assert source.x.values.ndim == 1
    assert source.y.values.ndim == 1
    assert source.z.values.ndim == 1
    assert np.array_equal(source.x.values, x)
    assert np.array_equal(source.y.values, y)
    assert np.array_equal(source.z.values, z)


def test_numpy_scattered_points_auto_x_y():
    """Test scattered point data with auto-generated x and y."""
    # Only z provided, x and y should be auto-generated as indices
    z = np.array([10, 20, 15, 25, 18])

    source = get_source(z, context=PlotContext.CARTESIAN_2D)

    # Should auto-generate 1D x and y as indices
    assert source.x.values.ndim == 1
    assert source.y.values.ndim == 1
    assert source.z.values.ndim == 1
    assert np.array_equal(source.x.values, np.array([0, 1, 2, 3, 4]))
    assert np.array_equal(source.y.values, np.array([0, 1, 2, 3, 4]))
    assert np.array_equal(source.z.values, z)


# =============================================================================
# PlotContext Tests (NEW FEATURE)
# =============================================================================


def test_numpy_context_cartesian_1d():
    """Test PlotContext.CARTESIAN_1D inference."""
    source = get_source([1, 2, 3], context=PlotContext.CARTESIAN_1D)
    # 1D data goes to y, x is generated
    assert source.x.values is not None
    assert source.y.values is not None
    assert source.z is None


def test_numpy_context_cartesian_2d():
    """Test PlotContext.CARTESIAN_2D inference."""
    source = get_source([[1, 2, 3], [4, 5, 6]], context=PlotContext.CARTESIAN_2D)
    # 2D data goes to z, x/y are generated as meshgrids
    assert source.x.values is not None
    assert source.y.values is not None
    assert source.z.values is not None


# =============================================================================
# Metadata Tests
# =============================================================================


def test_numpy_metadata():
    """Test metadata extraction from numpy source."""
    source = get_source(
        [1, 2, 3], metadata={"units": "meters", "long_name": "Distance"}
    )
    assert source.metadata("units") == "meters"
    assert source.metadata("long_name") == "Distance"


def test_numpy_metadata_default():
    """Test metadata default value."""
    source = get_source([1, 2, 3])
    assert source.metadata("nonexistent", "default") == "default"


def test_numpy_source_units():
    """Test units property."""
    source = get_source([1, 2, 3], metadata={"units": "m/s"})
    assert source.source_units == "m/s"


# =============================================================================
# Unit Conversion Tests (NEW FEATURE)
# =============================================================================


def test_numpy_unit_conversion_1d():
    """Test unit conversion for 1D data (y-values)."""
    # Note: numpy doesn't have built-in units, but we can pass target units
    source = get_source(
        [0, 10, 20],  # Celsius values
        metadata={"units": "degC"},
        units="K",  # Convert to Kelvin
        context=PlotContext.CARTESIAN_1D,
    )

    # y_values should be converted
    expected = np.array([273.15, 283.15, 293.15])
    assert np.allclose(source.y.values, expected)


def test_numpy_unit_conversion_2d():
    """Test unit conversion for 2D data (z-values)."""
    data = np.array([[0, 10], [20, 30]])  # Celsius
    source = get_source(
        data,
        metadata={"units": "degC"},
        units="K",
        context=PlotContext.CARTESIAN_2D,
    )

    # z_values should be converted
    expected = np.array([[273.15, 283.15], [293.15, 303.15]])
    assert np.allclose(source.z.values, expected)


def test_numpy_no_conversion_without_units():
    """Test that no conversion happens when units not specified."""
    source = get_source([1, 2, 3], context=PlotContext.CARTESIAN_1D)
    assert np.array_equal(source.y.values, np.array([1, 2, 3]))


# =============================================================================
# Matplotlib-style API Tests
# =============================================================================


def test_numpy_matplotlib_style_1d():
    """Test matplotlib-style API: get_source(y) for 1D plots."""
    y_data = np.array([1, 4, 2, 8, 5])
    source = get_source(y_data, context=PlotContext.CARTESIAN_1D)

    # Should auto-generate x as index
    assert np.array_equal(source.x.values, np.array([0, 1, 2, 3, 4]))
    assert np.array_equal(source.y.values, y_data)
    assert source.z is None


def test_numpy_matplotlib_style_2d():
    """Test matplotlib-style API: get_source(z) for 2D plots."""
    z_data = np.random.rand(5, 7)
    source = get_source(z_data, context=PlotContext.CARTESIAN_2D)

    # Should auto-generate x, y as meshgrids from shape
    assert source.x.values.shape == (5, 7)
    assert source.y.values.shape == (5, 7)
    assert np.array_equal(source.z.values, z_data)


# =============================================================================
# CRS Tests
# =============================================================================


def test_numpy_no_crs():
    """Test that numpy arrays have no CRS."""
    source = get_source([[1, 2, 3], [4, 5, 6]], context=PlotContext.GEOGRAPHIC_2D)
    # Numpy doesn't have CRS info, should return None or PlateCarree default
    crs = source.crs
    assert crs is None or str(crs) == "PlateCarree()"
