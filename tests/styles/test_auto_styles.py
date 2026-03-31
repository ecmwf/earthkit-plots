# Copyright 2025-, European Centre for Medium Range Weather Forecasts.
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

from pathlib import Path

import pytest
import yaml

from earthkit.plots.styles.auto import (
    _select_style_variant,
    _StyleLibraryCache,
    criteria_matches,
    list_styles,
    load_style,
)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


class MockedData:
    def __init__(self, metadata):
        self._metadata = metadata

    def metadata(self, key, default=None):
        return self._metadata.get(key, default)


def write_yaml(path: Path, content: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        yaml.dump(content, f)


# ---------------------------------------------------------------------------
# criteria_matches — existing parametrised suite
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "metadata,criteria,expected",
    [
        # Basic GRIB parameter matching
        ({"shortName": "2t", "levtype": "sfc"}, {"shortName": "2t"}, True),
        ({"shortName": "2t", "level": 2}, {"shortName": "msl"}, False),
        ({"shortName": "t", "level": 850}, {"shortName": "u", "level": 500}, False),
        # Empty cases
        ({}, {"shortName": "2t"}, False),
        ({}, {}, True),
        # None values in metadata or criteria
        ({"shortName": None, "level": 850}, {"shortName": "t"}, False),
        ({"shortName": "t", "level": None}, {"level": 850}, False),
        ({"shortName": None}, {"shortName": None}, False),
        # parameter lists - exact matches
        ({"param": ["130", "131"]}, {"param": ["130", "131"]}, True),
        ({"param": ["131", "130"]}, {"param": ["130", "131"]}, True),
        ({"shortName": ["t"]}, {"shortName": ["t"]}, True),
        # parameter lists - mismatches
        ({"param": ["130"]}, {"param": ["130", "131"]}, False),
        ({"shortName": "t"}, {"param": ["130", "131"]}, False),
        ({"param": ["130", "131", "132"]}, {"param": ["130", "131"]}, False),
        # Mixed type matching (string vs list) - GRIB parameters
        ({"shortName": "t"}, {"shortName": "t"}, True),
        ({"param": ["130"]}, {"param": "130"}, False),
        ({"shortName": "t"}, {"shortName": ["t"]}, True),
        # Complex combinations with lists
        (
            {"param": ["130", "131"], "levelist": [850, 500]},
            {"param": ["130", "131"], "levelist": [850, 500]},
            True,
        ),
        (
            {"param": ["130", "131"], "level": 850},
            {"param": "130", "level": 850},
            False,
        ),
        (
            {"shortName": ["t", "u"], "levelist": [850, 500]},
            {"shortName": ["t", "u"], "levelist": [500, 850]},
            True,
        ),
        # Multiple criteria keys - should match only if ALL keys match
        ({"shortName": "t", "level": 850}, {"shortName": "t", "level": 850}, True),
        ({"shortName": "t", "level": 850}, {"shortName": "t", "level": 500}, False),
        ({"shortName": "msl", "level": 0}, {"shortName": "t", "level": 850}, False),
        # String vs number matching - levels and parameters
        ({"level": "850"}, {"level": "850"}, True),
        ({"level": 850}, {"level": 850}, True),
        ({"level": "850"}, {"level": 850}, False),
        ({"param": "130"}, {"param": 130}, False),
        # GRIB type of level matching
        ({"levtype": "pl"}, {"levtype": "pl"}, True),
        ({"levtype": "sfc"}, {"levtype": "pl"}, False),
        ({"levtype": "heightAboveGround"}, {"levtype": "sfc"}, False),
        # Complex GRIB metadata scenarios
        (
            {"shortName": "10u", "levtype": "heightAboveGround", "level": 10},
            {"shortName": "10u"},
            True,
        ),
        (
            {"shortName": "10v", "levtype": "heightAboveGround", "level": 10},
            {"levtype": "sfc"},
            False,
        ),
        (
            {"shortName": "sp", "levtype": "sfc", "step": 0},
            {"levtype": "sfc", "step": 0},
            True,
        ),
        # Edge case: key exists but with empty list
        ({"param": []}, {"param": []}, True),
        ({"param": []}, {"param": ["130"]}, False),
        ({"shortName": ["t"]}, {"shortName": []}, False),
        # GRIB parameter name case variations
        ({"shortName": "T"}, {"shortName": "t"}, False),
        ({"shortName": "MSL"}, {"shortName": "msl"}, False),
        # Special GRIB parameters
        ({"shortName": "2t"}, {"shortName": "2t"}, True),
        ({"shortName": "10u"}, {"shortName": "10v"}, False),
        ({"shortName": "tp"}, {"shortName": "cp"}, False),
    ],
)
def test_criteria_matches(metadata, criteria, expected):
    assert criteria_matches(MockedData(metadata), criteria) == expected


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def fake_plugin_dir(tmp_path):
    identities_dir = tmp_path / "identities"
    styles_dir = tmp_path / "auto-styles"

    write_yaml(
        identities_dir / "temperature.yml",
        {"id": "temperature_2m", "criteria": [{"shortName": "2t"}]},
    )
    write_yaml(
        identities_dir / "pressure.yml",
        {"id": "msl", "criteria": [{"shortName": "msl"}]},
    )
    write_yaml(
        styles_dir / "temperature.yml",
        {
            "id": "temperature_2m",
            "optimal": "CELSIUS",
            "styles": {
                "CELSIUS": {
                    "name": "temperature-2m-celsius",
                    "type": "Style",
                    "colors": ["#0000ff", "#ff0000"],
                    "levels": [250.0, 260.0, 270.0],
                    "units": "celsius",
                    "extend": "both",
                },
                "KELVIN": {
                    "name": "temperature-2m-kelvin",
                    "type": "Style",
                    "colors": ["#00ff00", "#ffff00"],
                    "levels": [230.0, 240.0, 250.0],
                    "units": "K",
                    "extend": "both",
                },
            },
        },
    )
    write_yaml(
        styles_dir / "pressure.yml",
        {
            "id": "msl",
            "optimal": "HPA",
            "styles": {
                "HPA": {
                    "name": "mslp-hpa",
                    "type": "Style",
                    "colors": ["#ffffff", "#aaaaaa"],
                    "levels": [980.0, 1000.0, 1020.0],
                    "units": "hPa",
                    "extend": "both",
                },
            },
        },
    )
    return tmp_path


@pytest.fixture()
def fresh_cache():
    """Isolated _StyleLibraryCache instance — never shares state between tests."""
    return _StyleLibraryCache()


# ---------------------------------------------------------------------------
# _StyleLibraryCache — identity lookup
# ---------------------------------------------------------------------------


def _point_cache_at(cache, plugin_dir: Path, monkeypatch, key: str = "test-plugin"):
    """
    Redirect *cache* so that `_ensure_loaded` loads from *plugin_dir* instead
    of the real PLUGINS registry.  This is the correct way to test the public
    API — we exercise the full load + lookup path, not just the private loader.
    """
    monkeypatch.setattr(cache, "_current_plugin_key", lambda: key)
    monkeypatch.setattr(
        cache,
        "_resolve_plugin_paths",
        lambda: (plugin_dir / "identities", plugin_dir / "auto-styles"),
    )


class TestIdentityLookup:
    def test_finds_matching_identity(self, fresh_cache, fake_plugin_dir, monkeypatch):
        _point_cache_at(fresh_cache, fake_plugin_dir, monkeypatch)
        data = MockedData({"shortName": "2t"})
        assert fresh_cache.find_identity(data) == "temperature_2m"

    def test_returns_none_for_no_match(self, fresh_cache, fake_plugin_dir, monkeypatch):
        _point_cache_at(fresh_cache, fake_plugin_dir, monkeypatch)
        data = MockedData({"shortName": "unknown_var"})
        assert fresh_cache.find_identity(data) is None

    def test_first_match_wins(self, fresh_cache, tmp_path, monkeypatch):
        """Two overlapping identity files — first alphabetically must win."""
        write_yaml(
            tmp_path / "identities" / "a_first.yml",
            {"id": "first", "criteria": [{"shortName": "2t"}]},
        )
        write_yaml(
            tmp_path / "identities" / "b_second.yml",
            {"id": "second", "criteria": [{"shortName": "2t"}]},
        )
        # auto-styles dir must exist (even empty) so _load_style_configs doesn't error
        (tmp_path / "auto-styles").mkdir()
        _point_cache_at(fresh_cache, tmp_path, monkeypatch)
        data = MockedData({"shortName": "2t"})
        # Both match; the alphabetically-first file should win (sorted iterdir).
        assert fresh_cache.find_identity(data) == "first"

    def test_missing_identities_dir_handled_gracefully(self, fresh_cache, tmp_path, monkeypatch):
        # Point at a directory that has neither identities/ nor auto-styles/
        _point_cache_at(fresh_cache, tmp_path, monkeypatch)
        data = MockedData({"shortName": "2t"})
        assert fresh_cache.find_identity(data) is None


# ---------------------------------------------------------------------------
# _StyleLibraryCache — style config lookup
# ---------------------------------------------------------------------------


class TestStyleConfigLookup:
    def test_returns_correct_config(self, fresh_cache, fake_plugin_dir, monkeypatch):
        _point_cache_at(fresh_cache, fake_plugin_dir, monkeypatch)
        config = fresh_cache.get_style_config("temperature_2m")
        assert config is not None
        assert set(config["styles"]) == {"CELSIUS", "KELVIN"}

    def test_returns_none_for_unknown_id(self, fresh_cache, fake_plugin_dir, monkeypatch):
        _point_cache_at(fresh_cache, fake_plugin_dir, monkeypatch)
        assert fresh_cache.get_style_config("does_not_exist") is None

    def test_missing_styles_dir_handled_gracefully(self, fresh_cache, tmp_path, monkeypatch):
        _point_cache_at(fresh_cache, tmp_path, monkeypatch)
        assert fresh_cache.get_style_config("anything") is None


# ---------------------------------------------------------------------------
# _StyleLibraryCache — named styles
# ---------------------------------------------------------------------------


class TestNamedStyles:
    def test_lists_all_named_styles(self, fresh_cache, fake_plugin_dir):
        fresh_cache._load_named_styles_from(fake_plugin_dir / "auto-styles")
        names = fresh_cache.list_named_styles()
        assert "temperature-2m-celsius" in names
        assert "temperature-2m-kelvin" in names
        assert "mslp-hpa" in names

    def test_list_is_sorted(self, fresh_cache, fake_plugin_dir):
        fresh_cache._load_named_styles_from(fake_plugin_dir / "auto-styles")
        names = fresh_cache.list_named_styles()
        assert names == sorted(names)

    def test_get_named_style_returns_correct_dict(self, fresh_cache, fake_plugin_dir):
        fresh_cache._load_named_styles_from(fake_plugin_dir / "auto-styles")
        style_dict = fresh_cache.get_named_style("mslp-hpa")
        assert style_dict is not None
        assert style_dict["units"] == "hPa"

    def test_get_named_style_returns_none_for_unknown_name(self, fresh_cache, fake_plugin_dir):
        fresh_cache._load_named_styles_from(fake_plugin_dir / "auto-styles")
        assert fresh_cache.get_named_style("nonexistent-style") is None

    def test_duplicate_names_across_paths_kept_once(self, fresh_cache, tmp_path):
        """The same named style from two directories appears only once."""
        shared_style = {
            "id": "foo",
            "optimal": "FOO",
            "styles": {
                "FOO": {
                    "name": "shared-name",
                    "type": "Style",
                    "colors": ["#000000"],
                    "levels": [0, 1],
                    "units": "K",
                },
            },
        }
        seen: set[str] = set()
        for subdir in ("plugin_a", "plugin_b"):
            styles_dir = tmp_path / subdir
            write_yaml(styles_dir / "foo.yml", shared_style)
            fresh_cache._load_named_styles_from(styles_dir, seen)

        assert fresh_cache.list_named_styles().count("shared-name") == 1


# ---------------------------------------------------------------------------
# _StyleLibraryCache — invalidation
# ---------------------------------------------------------------------------


class TestCacheInvalidation:
    def test_invalidate_clears_all_state(self, fresh_cache, fake_plugin_dir, monkeypatch):
        # Populate via the public API (goes through _ensure_loaded).
        _point_cache_at(fresh_cache, fake_plugin_dir, monkeypatch)
        fresh_cache.find_identity(MockedData({"shortName": "2t"}))  # triggers load
        fresh_cache._load_named_styles_from(fake_plugin_dir / "auto-styles")

        assert len(fresh_cache._identities) > 0
        assert len(fresh_cache._style_configs) > 0
        assert len(fresh_cache._named_styles) > 0

        fresh_cache.invalidate()

        assert fresh_cache._identities == []
        assert fresh_cache._style_configs == {}
        assert fresh_cache._named_styles == {}
        assert fresh_cache._loaded_plugin is None
        assert fresh_cache._named_styles_loaded is False

    def test_named_styles_reload_after_invalidate(self, fresh_cache, fake_plugin_dir, monkeypatch):
        """Named styles should be re-indexed from disk after invalidation."""
        _point_cache_at(fresh_cache, fake_plugin_dir, monkeypatch)
        # Seed the named-styles index via the public API.
        monkeypatch.setattr(
            fresh_cache,
            "_load_named_styles",
            lambda: fresh_cache._load_named_styles_from(fake_plugin_dir / "auto-styles"),
        )
        assert "mslp-hpa" in fresh_cache.list_named_styles()

        fresh_cache.invalidate()
        # After invalidation the flag is cleared; next call should reload.
        monkeypatch.setattr(
            fresh_cache,
            "_load_named_styles",
            lambda: fresh_cache._load_named_styles_from(fake_plugin_dir / "auto-styles"),
        )
        assert "mslp-hpa" in fresh_cache.list_named_styles()

    def test_second_call_does_not_reload(self, fresh_cache, fake_plugin_dir, monkeypatch):
        """_ensure_loaded called twice for the same plugin key only loads once."""
        load_call_count = [0]
        original = fresh_cache._load_identities

        def counting_load(path):
            load_call_count[0] += 1
            original(path)

        monkeypatch.setattr(fresh_cache, "_load_identities", counting_load)
        _point_cache_at(fresh_cache, fake_plugin_dir, monkeypatch)

        fresh_cache._ensure_loaded()
        fresh_cache._ensure_loaded()

        assert load_call_count[0] == 1

    def test_invalidate_triggers_reload_on_next_access(self, fresh_cache, fake_plugin_dir, monkeypatch):
        load_call_count = [0]
        original = fresh_cache._load_identities

        def counting_load(path):
            load_call_count[0] += 1
            original(path)

        monkeypatch.setattr(fresh_cache, "_load_identities", counting_load)
        _point_cache_at(fresh_cache, fake_plugin_dir, monkeypatch)

        fresh_cache._ensure_loaded()
        assert load_call_count[0] == 1

        fresh_cache.invalidate()
        fresh_cache._ensure_loaded()
        assert load_call_count[0] == 2


# ---------------------------------------------------------------------------
# _StyleLibraryCache — plugin switching
# ---------------------------------------------------------------------------


class TestPluginSwitching:
    def test_reloads_when_plugin_key_changes(self, fresh_cache, tmp_path, monkeypatch):
        """
        Switching the active plugin key causes the identity index to reflect
        the new plugin's data.
        """
        plugin_a = tmp_path / "plugin_a"
        plugin_b = tmp_path / "plugin_b"

        for plugin_dir, short_name, style_id in [
            (plugin_a, "2t", "temp_a"),
            (plugin_b, "msl", "pres_b"),
        ]:
            write_yaml(
                plugin_dir / "identities" / "var.yml",
                {"id": style_id, "criteria": [{"shortName": short_name}]},
            )
            write_yaml(
                plugin_dir / "auto-styles" / "var.yml",
                {
                    "id": style_id,
                    "optimal": "ONLY",
                    "styles": {
                        "ONLY": {
                            "name": f"{style_id}-style",
                            "type": "Style",
                            "colors": [],
                            "levels": [],
                        }
                    },
                },
            )

        active_plugin = ["plugin_a"]

        monkeypatch.setattr(fresh_cache, "_current_plugin_key", lambda: active_plugin[0])
        monkeypatch.setattr(
            fresh_cache,
            "_resolve_plugin_paths",
            lambda: (
                tmp_path / active_plugin[0] / "identities",
                tmp_path / active_plugin[0] / "auto-styles",
            ),
        )

        data_2t = MockedData({"shortName": "2t"})
        data_msl = MockedData({"shortName": "msl"})

        # Plugin A loaded — finds 2t but not msl.
        assert fresh_cache.find_identity(data_2t) == "temp_a"
        assert fresh_cache.find_identity(data_msl) is None

        # Switch to plugin B and invalidate.
        active_plugin[0] = "plugin_b"
        fresh_cache.invalidate()

        # Plugin B loaded — finds msl but not 2t.
        assert fresh_cache.find_identity(data_msl) == "pres_b"
        assert fresh_cache.find_identity(data_2t) is None


# ---------------------------------------------------------------------------
# _select_style_variant — pure unit tests
# ---------------------------------------------------------------------------

_CELSIUS = {
    "name": "temp-celsius",
    "type": "Style",
    "units": "celsius",
    "colors": [],
    "levels": [],
}
_KELVIN = {
    "name": "temp-kelvin",
    "type": "Style",
    "units": "K",
    "colors": [],
    "levels": [],
}
_NOUNIT = {"name": "temp-none", "type": "Style", "colors": [], "levels": []}

_VARIANTS = {"CELSIUS": _CELSIUS, "KELVIN": _KELVIN, "NOUNIT": _NOUNIT}
_VARIANTS_UNITS_ONLY = {"CELSIUS": _CELSIUS, "KELVIN": _KELVIN}


class TestSelectStyleVariant:
    def test_exact_target_units_wins(self):
        assert _select_style_variant(_VARIANTS, "celsius", "K") is _CELSIUS

    def test_source_units_used_when_no_target_match(self):
        assert _select_style_variant(_VARIANTS_UNITS_ONLY, "hPa", "K") is _KELVIN

    def test_no_units_variant_is_last_resort(self):
        assert _select_style_variant(_VARIANTS, "hPa", "Pa") is _NOUNIT

    def test_returns_none_when_nothing_matches(self):
        assert _select_style_variant(_VARIANTS_UNITS_ONLY, "hPa", "Pa") is None

    def test_none_target_and_source_returns_no_units_variant(self):
        # Both None — are_equal(None, None) is True so the first pass matches
        # the first variant whose units is None (i.e. _NOUNIT).
        result = _select_style_variant(_VARIANTS, None, None)
        assert result is _NOUNIT

    def test_empty_variants_returns_none(self):
        assert _select_style_variant({}, "celsius", "celsius") is None


# ---------------------------------------------------------------------------
# Integration tests: load_style / list_styles against the real bundled library
# ---------------------------------------------------------------------------


class TestLoadStyleIntegration:
    def test_list_styles_returns_nonempty_sorted_list(self):
        names = list_styles()
        assert isinstance(names, list)
        assert len(names) > 0
        assert names == sorted(names)

    def test_load_style_returns_style_object(self):
        from earthkit.plots.styles import Style

        name = list_styles()[0]
        style = load_style(name)
        assert isinstance(style, Style)

    def test_load_style_raises_key_error_for_unknown_name(self):
        with pytest.raises(KeyError, match="no-such-style-xyz"):
            load_style("no-such-style-xyz")

    def test_load_style_kwargs_override_applied(self):
        """Kwargs passed to load_style are forwarded to the Style constructor."""
        from earthkit.plots.styles import Style

        name = list_styles()[0]
        style = load_style(name, legend_style="disjoint")
        assert isinstance(style, Style)
        assert style._legend_style == "disjoint"

    def test_repeated_list_styles_calls_return_same_result(self):
        """The cached result must be stable across repeated calls."""
        first = list_styles()
        second = list_styles()
        assert first == second

    def test_repeated_load_style_calls_return_equivalent_styles(self):
        """Two load_style calls for the same name produce equivalent Style objects."""
        name = list_styles()[0]
        style_a = load_style(name)
        style_b = load_style(name)
        # Style.__eq__ compares _levels and _colors.
        assert style_a == style_b


# ---------------------------------------------------------------------------
# use_preferred_units — Source.update_units and pipeline integration
# ---------------------------------------------------------------------------


class TestUsePreferredUnits:
    """
    Tests for the use_preferred_units feature.

    The expected behaviour is:
      1. guess_style(..., use_preferred_units=True) returns the optimal style
         with the preferred units (e.g. celsius), regardless of source units.
      2. Source.update_units() resets _generic_units and clears the z-dimension
         cache so that unit conversion is applied on the next .z access.
      3. The pipeline correctly converts data values when use_preferred_units is
         set and the source units differ from the preferred style units.
    """

    # ------------------------------------------------------------------
    # Source.update_units — unit tests
    # ------------------------------------------------------------------

    def test_update_units_sets_generic_units(self):
        import numpy as np
        import xarray as xr

        from earthkit.plots.sources import get_source

        data = xr.DataArray(
            np.array([[270.0, 280.0], [290.0, 300.0]]),
            dims=["latitude", "longitude"],
            coords={"latitude": [0.0, 10.0], "longitude": [0.0, 10.0]},
            attrs={"units": "K"},
        )
        source = get_source(data)
        source.update_units("celsius")
        assert source._generic_units == "celsius"

    def test_update_units_clears_z_dimension_cache(self):
        import numpy as np
        import xarray as xr

        from earthkit.plots.sources import get_source

        data = xr.DataArray(
            np.array([[270.0, 280.0], [290.0, 300.0]]),
            dims=["latitude", "longitude"],
            coords={"latitude": [0.0, 10.0], "longitude": [0.0, 10.0]},
            attrs={"units": "K"},
        )
        source = get_source(data)
        # Trigger caching of z
        _ = source.z
        assert source._z_dimension is not None

        source.update_units("celsius")
        assert source._z_dimension is None

    def test_update_units_conversion_applied_on_next_z_access(self):
        """After update_units, .z.values should contain converted data."""
        import numpy as np
        import xarray as xr

        from earthkit.plots.sources import get_source

        kelvin_values = np.array([[273.15, 283.15], [293.15, 303.15]])
        data = xr.DataArray(
            kelvin_values,
            dims=["latitude", "longitude"],
            coords={"latitude": [0.0, 10.0], "longitude": [0.0, 10.0]},
            attrs={"units": "K"},
        )
        source = get_source(data)
        source.update_units("celsius")

        celsius_values = source.z.values
        expected = kelvin_values - 273.15
        np.testing.assert_allclose(celsius_values, expected, atol=1e-6)

    # ------------------------------------------------------------------
    # guess_style with use_preferred_units — style selection
    # ------------------------------------------------------------------

    def test_guess_style_returns_optimal_style_units(self, fake_plugin_dir, fresh_cache, monkeypatch):
        """guess_style with use_preferred_units=True returns a Style with celsius units."""
        import numpy as np
        import xarray as xr

        from earthkit.plots.schemas import schema
        from earthkit.plots.sources import get_source
        from earthkit.plots.styles.auto import guess_style

        _point_cache_at(fresh_cache, fake_plugin_dir, monkeypatch)
        monkeypatch.setattr("earthkit.plots.styles.auto._cache", fresh_cache)

        data = xr.DataArray(
            np.array([[270.0, 280.0], [290.0, 300.0]]),
            dims=["latitude", "longitude"],
            coords={"latitude": [0.0, 10.0], "longitude": [0.0, 10.0]},
            attrs={"units": "K", "shortName": "2t"},
        )
        source = get_source(data)

        with schema.set(use_preferred_units=True):
            style = guess_style(source)

        assert style._units == "celsius"

    def test_guess_style_preferred_units_does_not_override_style_units(self, fake_plugin_dir, fresh_cache, monkeypatch):
        """
        With use_preferred_units=True, guess_style must NOT override the style
        units with the source units (the old bug: returned a Style with units="K").
        """
        import numpy as np
        import xarray as xr

        from earthkit.plots.schemas import schema
        from earthkit.plots.sources import get_source
        from earthkit.plots.styles.auto import guess_style

        _point_cache_at(fresh_cache, fake_plugin_dir, monkeypatch)
        monkeypatch.setattr("earthkit.plots.styles.auto._cache", fresh_cache)

        data = xr.DataArray(
            np.array([[270.0, 280.0], [290.0, 300.0]]),
            dims=["latitude", "longitude"],
            coords={"latitude": [0.0, 10.0], "longitude": [0.0, 10.0]},
            attrs={"units": "K", "shortName": "2t"},
        )
        source = get_source(data)

        with schema.set(use_preferred_units=True):
            style = guess_style(source)

        # The style's units must be the preferred celsius, not the source K.
        assert style._units != "K"
        assert style._units == "celsius"

    # ------------------------------------------------------------------
    # Full pipeline: update_units converts data values
    # ------------------------------------------------------------------

    def test_pipeline_converts_values_with_preferred_units(self, fake_plugin_dir, fresh_cache, monkeypatch):
        """
        End-to-end: build a Kelvin source, run guess_style, call update_units,
        and verify .z.values are in celsius.
        """
        import numpy as np
        import xarray as xr

        from earthkit.plots.schemas import schema
        from earthkit.plots.sources import get_source
        from earthkit.plots.styles.auto import guess_style

        _point_cache_at(fresh_cache, fake_plugin_dir, monkeypatch)
        monkeypatch.setattr("earthkit.plots.styles.auto._cache", fresh_cache)

        kelvin_values = np.array([[273.15, 283.15], [293.15, 303.15]])
        data = xr.DataArray(
            kelvin_values,
            dims=["latitude", "longitude"],
            coords={"latitude": [0.0, 10.0], "longitude": [0.0, 10.0]},
            attrs={"units": "K", "shortName": "2t"},
        )
        source = get_source(data)

        with schema.set(use_preferred_units=True):
            style = guess_style(source)

        # Simulate what the pipeline does after configure_style.
        from earthkit.plots.metadata.units import are_equal

        if style._units is not None and not are_equal(style._units, source.source_units):
            source.update_units(style._units)

        celsius_values = source.z.values
        expected = kelvin_values - 273.15
        np.testing.assert_allclose(celsius_values, expected, atol=1e-6)
        assert source.z.units == "celsius"
