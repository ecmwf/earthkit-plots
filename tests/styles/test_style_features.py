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
from earthkit.plots.styles import Style


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

            deprecation_warnings = [
                warning
                for warning in w
                if issubclass(warning.category, DeprecationWarning) and "auto_style" in str(warning.message)
            ]
            assert len(deprecation_warnings) > 0
            assert "style='auto'" in str(deprecation_warnings[-1].message)

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

    def test_style_auto_with_overrides(self, sample_data):
        """Test that style='auto' works with parameter overrides."""
        chart = Subplot()
        chart.pcolormesh(sample_data, style="auto", levels=[250, 260, 270, 280, 290])

        # Should have auto-detected a style and applied the level overrides
        assert len(chart.layers) == 1
        used_style = chart.layers[0].style
        assert used_style._levels._levels == [250, 260, 270, 280, 290]


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

    def test_with_overrides_preserves_step_config(self):
        """Test that with_overrides preserves step-based level configuration."""
        # Create a style with step-based levels
        base_style = Style(colors="viridis", levels={"step": 4})

        # Override colors but keep the step configuration
        override_style = base_style.with_overrides(colors="plasma")

        # Base style should be unchanged
        assert base_style._levels._step == 4

        # Override style should preserve the step configuration
        assert override_style._levels._step == 4
        assert override_style._colors == "plasma"


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
        style_celsius = Style(units="celsius", levels=[-10, 0, 10, 20, 30], colors="coolwarm")

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

        style_combo = Style(units="celsius", levels=[-30, -10, 10, 30], colors="RdBu_r")

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


class TestCmapAlias:
    """Test that cmap and colors are treated as aliases."""

    def test_cmap_overrides_style_colors(self):
        """Test that cmap parameter overrides colors in style."""
        sample_data = xr.DataArray(
            np.random.rand(10, 10) * 50 + 250,
            dims=["lat", "lon"],
            coords={"lat": np.linspace(-90, 90, 10), "lon": np.linspace(-180, 180, 10)},
            attrs={"units": "K"},
        )

        original_style = Style(colors="viridis", levels=[250, 260, 270, 280, 290])

        chart = Subplot()
        chart.pcolormesh(sample_data, style=original_style, cmap="plasma")

        # Original style should be unchanged
        assert original_style._colors == "viridis"

        # Used style should have cmap (colors) overridden
        used_style = chart.layers[0].style
        assert used_style._colors == "plasma"

    def test_cmap_and_colors_together_raises_error(self):
        """Test that using both cmap and colors raises an error."""
        sample_data = xr.DataArray(
            np.random.rand(10, 10) * 50 + 250,
            dims=["lat", "lon"],
            coords={"lat": np.linspace(-90, 90, 10), "lon": np.linspace(-180, 180, 10)},
            attrs={"units": "K"},
        )

        with pytest.raises(ValueError, match="Cannot specify both 'cmap' and 'colors'"):
            chart = Subplot()
            chart.pcolormesh(sample_data, cmap="viridis", colors="plasma")

    def test_cmap_with_auto_style(self):
        """Test that cmap works with style='auto'."""
        sample_data = xr.DataArray(
            np.random.rand(10, 10) * 50 + 250,
            dims=["lat", "lon"],
            coords={"lat": np.linspace(-90, 90, 10), "lon": np.linspace(-180, 180, 10)},
            attrs={"units": "K"},
        )

        chart = Subplot()
        chart.pcolormesh(sample_data, style="auto", cmap="coolwarm")

        # Should have auto-detected a style and applied the cmap
        used_style = chart.layers[0].style
        assert used_style._colors == "coolwarm"

    def test_style_init_with_cmap(self):
        """Test that Style can be initialized with cmap parameter."""
        style = Style(cmap="viridis", levels=[0, 10, 20])
        assert style._colors == "viridis"

    def test_style_init_with_both_raises_error(self):
        """Test that initializing Style with both cmap and colors raises an error."""
        with pytest.raises(ValueError, match="Cannot specify both 'colors' and 'cmap'"):
            Style(colors="viridis", cmap="plasma")

    def test_with_overrides_cmap(self):
        """Test that with_overrides accepts cmap parameter."""
        base_style = Style(colors="viridis", levels=[0, 10, 20])
        override_style = base_style.with_overrides(cmap="plasma")

        # Base style should be unchanged
        assert base_style._colors == "viridis"

        # Override style should have new colors
        assert override_style._colors == "plasma"

    def test_with_overrides_both_raises_error(self):
        """Test that with_overrides raises error for both cmap and colors."""
        base_style = Style(colors="viridis", levels=[0, 10, 20])

        with pytest.raises(ValueError, match="Cannot specify both 'cmap' and 'colors'"):
            base_style.with_overrides(cmap="plasma", colors="coolwarm")


class TestColormapObject:
    """Test that matplotlib Colormap objects work as colors/cmap arguments."""

    def test_colormap_object_via_colors(self):
        """A Colormap object passed as ``colors`` produces valid cmap/norm."""
        import matplotlib as mpl

        style = Style(colors=mpl.cm.viridis, levels=[0, 10, 20, 30])
        kwargs = style.to_matplotlib_kwargs(np.random.rand(10, 10) * 30)
        assert isinstance(kwargs["cmap"], mpl.colors.Colormap)
        assert kwargs["norm"] is not None

    def test_colormap_object_via_cmap_alias(self):
        """A Colormap object passed as ``cmap`` produces valid cmap/norm."""
        import matplotlib as mpl

        style = Style(cmap=mpl.cm.viridis, levels=[0, 10, 20, 30])
        kwargs = style.to_matplotlib_kwargs(np.random.rand(10, 10) * 30)
        assert isinstance(kwargs["cmap"], mpl.colors.Colormap)
        assert kwargs["norm"] is not None

    def test_colormap_object_with_extend_both(self):
        """Issue #204 repro: Colormap object with extend='both' and levels."""
        import matplotlib as mpl

        style = Style(
            cmap=mpl.cm.RdBu,
            levels=[-3, -1, 1, 3],
            normalize=False,
            extend="both",
        )
        kwargs = style.to_matplotlib_kwargs(np.random.rand(10, 10) * 6 - 3)
        assert isinstance(kwargs["cmap"], mpl.colors.Colormap)

    def test_linear_segmented_colormap_object(self):
        """A LinearSegmentedColormap object (e.g. plt.cm.RdBu) works."""
        import matplotlib as mpl

        assert isinstance(mpl.cm.RdBu, mpl.colors.LinearSegmentedColormap)
        style = Style(cmap=mpl.cm.RdBu, levels=[-3, -1, 1, 3])
        kwargs = style.to_matplotlib_kwargs(np.random.rand(10, 10) * 6 - 3)
        assert isinstance(kwargs["cmap"], mpl.colors.Colormap)
        assert kwargs["norm"] is not None

    def test_listed_colormap_object(self):
        """A ListedColormap object (e.g. plt.cm.viridis) works."""
        import matplotlib as mpl

        assert isinstance(mpl.cm.viridis, mpl.colors.ListedColormap)
        style = Style(cmap=mpl.cm.viridis, levels=[0, 10, 20, 30])
        kwargs = style.to_matplotlib_kwargs(np.random.rand(10, 10) * 30)
        assert isinstance(kwargs["cmap"], mpl.colors.Colormap)
        assert kwargs["norm"] is not None

    def test_colormap_object_matches_named_string(self):
        """A Colormap object samples identically to its registered name."""
        import matplotlib as mpl

        from earthkit.plots.styles.colors import expand

        levels = [0, 10, 20, 30]
        from_object = expand(mpl.cm.viridis, levels)
        from_name = expand("viridis", levels)
        assert np.allclose(np.array(from_object), np.array(from_name))

    def test_colormap_object_plots_without_error(self):
        """End-to-end: a Colormap object plots through pcolormesh."""
        import matplotlib as mpl

        sample_data = xr.DataArray(
            np.random.rand(10, 10) * 50 + 250,
            dims=["lat", "lon"],
            coords={"lat": np.linspace(-90, 90, 10), "lon": np.linspace(-180, 180, 10)},
            attrs={"units": "K"},
        )
        style = Style(cmap=mpl.cm.plasma, levels=[250, 260, 270, 280, 290])
        chart = Subplot()
        chart.pcolormesh(sample_data, style=style)


class TestVminVmax:
    """Test vmin/vmax support on Style."""

    def test_vmin_vmax_stored(self):
        """Test that vmin/vmax are stored on the Style."""
        style = Style(colors="viridis", vmin=0, vmax=100)
        assert style._vmin == 0
        assert style._vmax == 100

    def test_to_matplotlib_kwargs_produces_normalize(self):
        """Test that vmin/vmax produces a Normalize norm, not BoundaryNorm."""
        import matplotlib as mpl

        style = Style(colors="viridis", vmin=0.0, vmax=100.0)
        data = np.random.rand(10, 10) * 100
        kwargs = style.to_matplotlib_kwargs(data)

        assert isinstance(kwargs["norm"], mpl.colors.Normalize)
        assert not isinstance(kwargs["norm"], mpl.colors.BoundaryNorm)
        assert kwargs["norm"].vmin == 0.0
        assert kwargs["norm"].vmax == 100.0

    def test_to_matplotlib_kwargs_no_levels_key(self):
        """Test that vmin/vmax path does not include a 'levels' key."""
        style = Style(colors="viridis", vmin=0, vmax=50)
        data = np.random.rand(5, 5) * 50
        kwargs = style.to_matplotlib_kwargs(data)
        assert "levels" not in kwargs

    def test_vmin_only_uses_data_max(self):
        """Test that only vmin set uses data max for vmax."""
        import matplotlib as mpl

        data = np.ones((5, 5)) * 80.0
        style = Style(colors="viridis", vmin=10.0)
        kwargs = style.to_matplotlib_kwargs(data)

        assert isinstance(kwargs["norm"], mpl.colors.Normalize)
        assert kwargs["norm"].vmin == 10.0
        assert kwargs["norm"].vmax == pytest.approx(80.0)

    def test_vmax_only_uses_data_min(self):
        """Test that only vmax set uses data min for vmin."""
        import matplotlib as mpl

        data = np.ones((5, 5)) * 20.0
        style = Style(colors="viridis", vmax=90.0)
        kwargs = style.to_matplotlib_kwargs(data)

        assert isinstance(kwargs["norm"], mpl.colors.Normalize)
        assert kwargs["norm"].vmax == 90.0
        assert kwargs["norm"].vmin == pytest.approx(20.0)

    def test_levels_win_over_vmin_vmax(self):
        """Test that explicit levels take precedence over vmin/vmax."""
        import matplotlib as mpl

        style = Style(colors="viridis", levels=[0, 25, 50, 75, 100], vmin=-999, vmax=999)
        data = np.random.rand(5, 5) * 100
        kwargs = style.to_matplotlib_kwargs(data)

        assert isinstance(kwargs["norm"], mpl.colors.BoundaryNorm)
        assert "levels" in kwargs

    def test_get_config_roundtrip(self):
        """Test that vmin/vmax survive a _get_config round-trip."""
        style = Style(colors="plasma", vmin=-50, vmax=50)
        config = style._get_config()
        assert config["vmin"] == -50
        assert config["vmax"] == 50

        restored = Style(**config)
        assert restored._vmin == -50
        assert restored._vmax == 50

    def test_with_overrides_preserves_vmax(self):
        """Test that with_overrides of vmin preserves vmax."""
        base = Style(colors="viridis", vmin=0, vmax=100)
        overridden = base.with_overrides(vmin=10)
        assert overridden._vmin == 10
        assert overridden._vmax == 100

    def test_default_style_still_uses_boundary_norm(self):
        """Test that a style without vmin/vmax still produces BoundaryNorm."""
        import matplotlib as mpl

        style = Style(colors="viridis", levels=[0, 25, 50, 75, 100])
        data = np.random.rand(5, 5) * 100
        kwargs = style.to_matplotlib_kwargs(data)
        assert isinstance(kwargs["norm"], mpl.colors.BoundaryNorm)
