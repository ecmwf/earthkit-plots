# Copyright 2026-, European Centre for Medium Range Weather Forecasts.
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

import warnings

import numpy as np
import pytest
import xarray as xr

from earthkit.plots import Subplot
from earthkit.plots.styles import Contour, Style


@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    return xr.DataArray(
        np.random.rand(10, 10) * 50 + 250,
        dims=["lat", "lon"],
        coords={"lat": np.linspace(-90, 90, 10), "lon": np.linspace(-180, 180, 10)},
        attrs={"units": "K"},
    )


class TestStyleAuto:
    """Test style='auto' functionality."""

    def test_style_auto_works(self, sample_data):
        """Test that style='auto' works correctly."""
        chart = Subplot()
        chart.pcolormesh(sample_data, style="auto")
        assert len(chart.layers) == 1

    def test_auto_style_deprecated(self, sample_data):
        """Test that auto_style=True shows deprecation warning."""
        chart = Subplot()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            chart.pcolormesh(sample_data, auto_style=True)

            assert len(w) > 0
            assert issubclass(w[-1].category, DeprecationWarning)
            assert "auto_style" in str(w[-1].message)
            assert "style='auto'" in str(w[-1].message)

    def test_style_auto_equivalence(self, sample_data):
        """Test that style='auto' and auto_style=True produce equivalent results."""
        chart1 = Subplot()
        chart2 = Subplot()

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            chart1.pcolormesh(sample_data, style="auto")
            chart2.pcolormesh(sample_data, auto_style=True)

        # Both should have created layers with styles
        assert len(chart1.layers) == 1
        assert len(chart2.layers) == 1


class TestStyleOverrides:
    """Test style override functionality."""

    def test_override_levels(self, sample_data):
        """Test overriding levels in a style."""
        original_style = Style(colors="viridis", levels=[0, 10, 20, 30, 40])
        original_levels = original_style._levels._levels

        chart = Subplot()
        chart.pcolormesh(sample_data, style=original_style, levels=[250, 260, 270, 280, 290])

        # Original style should be unchanged
        assert original_style._levels._levels == original_levels

        # Used style should have overridden levels
        used_style = chart.layers[0].style
        assert used_style._levels._levels == [250, 260, 270, 280, 290]

    def test_override_colors(self, sample_data):
        """Test overriding colors in a style."""
        original_style = Style(colors="plasma", levels=[250, 270, 290])
        original_colors = original_style._colors

        chart = Subplot()
        chart.pcolormesh(sample_data, style=original_style, colors="coolwarm")

        # Original style colors should be unchanged
        assert original_style._colors == original_colors

        # Used style should have overridden colors
        used_style = chart.layers[0].style
        assert used_style._colors == "coolwarm"

    def test_no_override_no_copy(self, sample_data):
        """Test that using style without overrides doesn't create a copy."""
        original_style = Style(colors="inferno", levels=[250, 270, 290])

        chart = Subplot()
        chart.pcolormesh(sample_data, style=original_style)

        used_style = chart.layers[0].style
        assert used_style._levels._levels == [250, 270, 290]

    def test_with_overrides_method(self):
        """Test the with_overrides method directly."""
        base_style = Style(colors="jet", levels=[0, 100, 200])
        override_style = base_style.with_overrides(levels=[0, 50, 100, 150, 200])

        # Base style should be unchanged
        assert base_style._levels._levels == [0, 100, 200]

        # Override style should have new levels
        assert override_style._levels._levels == [0, 50, 100, 150, 200]
        

class TestStyleUnits:
    """Test automatic units from styles."""

    def test_units_from_style(self):
        """Test that units from style are used for unit conversion."""
        # Create data in Kelvin
        data_kelvin = xr.DataArray(
            np.array([[273.15, 283.15], [293.15, 303.15]]),
            dims=["lat", "lon"],
            coords={"lat": [0, 10], "lon": [0, 10]},
            attrs={"units": "K"},
        )

        # Create style with Celsius units
        style_celsius = Style(
            units="celsius", levels=[-10, 0, 10, 20, 30], colors="coolwarm"
        )

        chart = Subplot()
        chart.pcolormesh(data_kelvin, style=style_celsius)

        # Style units should be preserved
        layer = chart.layers[0]
        assert layer.style._units == "celsius"

        # Data should be converted to Celsius (approximately 0, 10, 20, 30)
        z_values = layer.sources[0].z.values
        assert z_values.min() > -5  # Should be around 0°C
        assert z_values.max() < 35  # Should be around 30°C


    def test_style_units_with_level_override(self):
        """Test that units from style work with level overrides."""
        data_kelvin = xr.DataArray(
            np.random.rand(5, 5) * 30 + 273.15,
            dims=["lat", "lon"],
            coords={"lat": np.arange(5), "lon": np.arange(5)},
            attrs={"units": "K"},
        )

        style_combo = Style(
            units="celsius", levels=[-30, -10, 10, 30], colors="RdBu_r"
        )

        chart = Subplot()
        # Override levels but keep units from style
        chart.pcolormesh(data_kelvin, style=style_combo, levels=[-5, 5, 15, 25])

        layer = chart.layers[0]

        # Original style should be unchanged
        assert style_combo._levels._levels == [-30, -10, 10, 30]
        assert style_combo._units == "celsius"

        # Used style should have overridden levels but preserved units
        assert layer.style._levels._levels == [-5, 5, 15, 25]
        assert layer.style._units == "celsius"

        # Data should be converted to Celsius
        z_values = layer.sources[0].z.values
        assert z_values.min() > -5
        assert z_values.max() < 35
