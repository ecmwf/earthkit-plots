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

from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

import yaml

from earthkit.plots import styles
from earthkit.plots._plugins import PLUGINS
from earthkit.plots.metadata.units import are_equal
from earthkit.plots.schemas import schema

METADATA = dict[str, Any | Sequence[Any]]

# Colormaps cycled through when no auto-style is found for a variable.
# Variables are assigned a cmap in the order they are first encountered.
_FALLBACK_CMAPS = ["plasma", "viridis", "pink", "copper"]
_fallback_cmap_assignments: dict[str, str] = {}
# One Style instance per variable name so that the same variable always maps to
# the same object (legend deduplication uses ==), while two different variables
# that happen to share a cmap are still distinct objects.
_fallback_style_cache: dict[str, "styles.Style"] = {}
_VariableFallbackStyle = None  # built lazily after styles.Style is available


def _get_variable_fallback_style_class():
    """Return _VariableFallbackStyle, constructing it on first call.

    Deferred to avoid a circular import: auto.py is imported by
    styles/__init__.py before styles.Style is defined.
    """
    global _VariableFallbackStyle
    if _VariableFallbackStyle is None:

        class _VFS(styles.Style):
            """Fallback Style that compares by identity so two variables sharing
            the same cmap are never merged into one legend entry.
            """

            def __eq__(self, other):
                return self is other

            def __hash__(self):
                return id(self)

        _VariableFallbackStyle = _VFS
    return _VariableFallbackStyle


def criteria_matches(data, criteria: METADATA) -> bool:
    """Test if the metadata matches the criteria."""
    for key, value in criteria.items():
        metadata_value = data.metadata(key, None)
        if metadata_value is None:
            break

        if all(map(lambda x: isinstance(x, Iterable), (metadata_value, value))):
            if set(value) != set(metadata_value):
                break
        elif value != metadata_value:
            break
    else:
        return True
    return False


def _fallback_style(data):
    """
    Return a :class:`~earthkit.plots.styles.Style` with a per-variable
    fallback colormap.  Variables are assigned a cmap from ``_FALLBACK_CMAPS``
    in the order they are first seen; once the list is exhausted, cmaps cycle.
    Variables that don't expose a recognisable name all share the last fallback
    slot (same behaviour as the old ``DEFAULT_STYLE``).

    Each variable gets its own cached :class:`_VariableFallbackStyle` instance.
    Because that subclass compares by identity (not value), two variables that
    happen to share a cmap are never incorrectly merged into the same legend.
    """
    var_name = None
    for attr in ("name", "short_name", "param"):
        try:
            val = data.metadata(attr, None)
            if val:
                var_name = str(val)
                break
        except Exception:
            pass

    if var_name is None:
        return styles.DEFAULT_STYLE

    if var_name not in _fallback_style_cache:
        if var_name not in _fallback_cmap_assignments:
            idx = len(_fallback_cmap_assignments) % len(_FALLBACK_CMAPS)
            _fallback_cmap_assignments[var_name] = _FALLBACK_CMAPS[idx]
        cls = _get_variable_fallback_style_class()
        _fallback_style_cache[var_name] = cls(colors=_fallback_cmap_assignments[var_name])

    return _fallback_style_cache[var_name]


# ---------------------------------------------------------------------------
# Style library cache
# ---------------------------------------------------------------------------


class _StyleLibraryCache:
    """
    Lazy, invalidatable cache for the YAML-based style library.

    Motivation
    ----------
    ``guess_style()`` and ``load_style()`` previously scanned all identity and
    auto-style YAML files from disk on **every call**.  With ~100 files in each
    directory this adds measurable latency in notebooks where the same variable
    is plotted many times.

    This cache loads each plugin's YAML files exactly once per Python session
    (or after an explicit :meth:`invalidate` call) and exposes fast in-memory
    lookup methods.

    Thread safety
    -------------
    The cache is populated in a single-threaded context (notebook / script) and
    is never written to after ``_load()`` completes, so no locking is required.
    """

    def __init__(self):
        # Keyed by plugin name; each value is the paths dict from PLUGINS.
        self._loaded_plugin: str | None = None

        # List of (criteria_list, identity_id) pairs — order preserved so that
        # the first match wins, exactly as the original glob loop did.
        self._identities: list[tuple[list[dict], str]] = []

        # identity_id → full style_config dict (contains "styles", "optimal", …)
        self._style_configs: dict[str, dict] = {}

        # name → style_dict for named styles (across ALL plugins, dedup by path).
        # Loaded once independently of the active plugin (all plugins contribute).
        self._named_styles: dict[str, dict] = {}
        self._named_styles_loaded: bool = False

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def invalidate(self):
        """Discard all cached data so the next access reloads from disk."""
        self._loaded_plugin = None
        self._identities.clear()
        self._style_configs.clear()
        self._named_styles.clear()
        self._named_styles_loaded = False

    def find_identity(self, data) -> str | None:
        """Return the identity id whose criteria first match *data*, or ``None``."""
        self._ensure_loaded()
        for criteria_list, identity_id in self._identities:
            if any(criteria_matches(data, c) for c in criteria_list):
                return identity_id
        return None

    def get_style_config(self, identity_id: str) -> dict | None:
        """Return the full style config dict for *identity_id*, or ``None``."""
        self._ensure_loaded()
        return self._style_configs.get(identity_id)

    def get_named_style(self, name: str) -> dict | None:
        """Return the raw style dict for the given *name*, or ``None``."""
        self._ensure_loaded_named_styles()
        return self._named_styles.get(name)

    def list_named_styles(self) -> list[str]:
        """Return a sorted list of all known named-style names."""
        self._ensure_loaded_named_styles()
        return sorted(self._named_styles)

    # ------------------------------------------------------------------
    # Internal loading
    # ------------------------------------------------------------------

    def _current_plugin_key(self) -> str:
        """Derive a cache key from the active style_library setting."""
        return str(schema.style_library)

    def _resolve_plugin_paths(self) -> tuple[Path, Path]:
        """Return (identities_path, styles_path) for the active plugin."""
        if schema.style_library not in PLUGINS:
            path = Path(schema.style_library).expanduser()
            return path / "identities", path / "auto-styles"
        plugin = PLUGINS[schema.style_library]
        return plugin["identities"], plugin["styles"]

    def _ensure_loaded(self):
        """Load identity + style-config data if the active plugin has changed."""
        key = self._current_plugin_key()
        if self._loaded_plugin == key:
            return

        self._identities.clear()
        self._style_configs.clear()

        identities_path, styles_path = self._resolve_plugin_paths()
        self._load_identities(identities_path)
        self._load_style_configs(styles_path)
        self._loaded_plugin = key

    def _ensure_loaded_named_styles(self):
        """Load named-style index across ALL plugins (done once per session)."""
        if self._named_styles_loaded:
            return
        self._load_named_styles()
        self._named_styles_loaded = True

    def _load_identities(self, identities_path: Path):
        if identities_path is None or not identities_path.is_dir():
            return
        for fpath in sorted(identities_path.iterdir()):
            if not fpath.is_file():
                continue
            with fpath.open() as f:
                config = yaml.load(f, Loader=yaml.SafeLoader)
            self._identities.append((config["criteria"], config["id"]))

    def _load_style_configs(self, styles_path: Path):
        if styles_path is None or not styles_path.is_dir():
            return
        for fpath in styles_path.iterdir():
            if not fpath.is_file():
                continue
            with fpath.open() as f:
                config = yaml.load(f, Loader=yaml.SafeLoader)
            self._style_configs[config["id"]] = config

    def _load_named_styles(self):
        """Index named-style variants from every registered plugin directory."""
        seen_paths: set[str] = set()
        for plugin_paths in PLUGINS.values():
            styles_path = plugin_paths["styles"]
            if styles_path is None or not styles_path.is_dir():
                continue
            for fpath in sorted(styles_path.iterdir()):
                fpath_str = str(fpath)
                if not fpath.is_file() or fpath_str in seen_paths:
                    continue
                seen_paths.add(fpath_str)
                with fpath.open() as f:
                    config = yaml.load(f, Loader=yaml.SafeLoader)
                for style_dict in config.get("styles", {}).values():
                    name = style_dict.get("name")
                    if name and name not in self._named_styles:
                        self._named_styles[name] = style_dict

    def _load_named_styles_from(self, styles_path: Path, seen_paths: set[str] | None = None):
        """
        Index named-style variants from a single *styles_path* directory.

        This is a test helper — production code goes through :meth:`_load_named_styles`
        which handles all plugins.  Tests call this directly to load from an
        isolated ``tmp_path`` directory without touching the real PLUGINS registry.

        Parameters
        ----------
        styles_path:
            Directory containing auto-style YAML files.
        seen_paths:
            Optional deduplication set shared across multiple calls (e.g. when
            a test simulates multiple plugin directories).
        """
        if styles_path is None or not styles_path.is_dir():
            return
        for fpath in sorted(styles_path.iterdir()):
            fpath_str = str(fpath)
            if not fpath.is_file():
                continue
            if seen_paths is not None:
                if fpath_str in seen_paths:
                    continue
                seen_paths.add(fpath_str)
            with fpath.open() as f:
                config = yaml.load(f, Loader=yaml.SafeLoader)
            for style_dict in config.get("styles", {}).values():
                name = style_dict.get("name")
                if name and name not in self._named_styles:
                    self._named_styles[name] = style_dict


# Module-level singleton — shared across all callers in the same process.
_cache = _StyleLibraryCache()


def _select_style_variant(style_variants: dict, target_units: str | None, source_units: str | None) -> dict | None:
    """
    Pick the best matching style variant dict for the given units.

    Selection priority:
    1. Exact match on *target_units*
    2. Exact match on *source_units*
    3. Any variant that carries no ``units`` key (unit-agnostic)
    4. ``None`` — caller should fall back to the default style

    Parameters
    ----------
    style_variants:
        Mapping of variant key → style dict, as stored in the YAML
        ``styles:`` block.
    target_units:
        The units the caller wants to plot in (may be ``None``).
    source_units:
        The native units of the data (may be ``None``).

    Returns
    -------
    dict or None
        The chosen style variant dict, or ``None`` if no match was found.
    """
    candidates = list(style_variants.values())

    for style in candidates:
        if are_equal(style.get("units"), target_units):
            return style

    for style in candidates:
        if are_equal(style.get("units"), source_units):
            return style

    for style in candidates:
        if "units" not in style:
            return style

    return None


def guess_style(data, units=None, **kwargs):
    """
    Guess the style to be applied to the data based on its metadata.

    The style is guessed by comparing the metadata of the data to the identities
    and styles in the style library. The first identity that matches the metadata
    is used to select the style. If the style library is not set or no identity
    matches the metadata, the default style is returned.

    Parameters
    ----------
    data : earthkit.plots.sources.Source
        The data object containing the metadata.
    units : str, optional
        The target units of the plot. If these do not match the units of the
        data, the data will be converted to the target units and the style
        will be adjusted accordingly.
    """
    # Use the source's native units (before any conversion) to pick the style
    # variant. The caller-supplied `units` is the *target* units and is used
    # below to select the matching style variant and to label the colorbar.
    source_units = data.source_units
    if units is None:
        units = source_units

    if not schema.automatic_styles or schema.style_library is None:
        return styles.DEFAULT_STYLE

    identity = _cache.find_identity(data)
    if identity is None:
        return _fallback_style(data)

    style_config = _cache.get_style_config(identity)
    if style_config is None:
        return _fallback_style(data)

    style_variants = style_config["styles"]

    if schema.use_preferred_units:
        style = style_variants[style_config["optimal"]]
    else:
        style = _select_style_variant(style_variants, units, source_units)
        if style is None:
            return _fallback_style(data)

        # If the caller requested specific target units that differ from the
        # style variant's own units, override so the colorbar label reflects
        # the actual plotted units (unit conversion is handled by Source).
        if units is not None and not are_equal(units, style.get("units")):
            kwargs.setdefault("units", units)

    return styles.Style.from_dict({**style, **kwargs})


def load_style(name, **kwargs):
    """
    Load a named style by its user-facing name.

    Style names are defined in the ``name`` field of each style variant in the
    auto-styles YAML files (e.g. ``temperature-2m-turbo-celsius``).  The full
    list of available names can be retrieved with :func:`list_styles`.

    Parameters
    ----------
    name : str
        The name of the style to load, as shown in the styles gallery.
    **kwargs
        Additional keyword arguments passed to the ``Style`` constructor,
        allowing individual parameters to be overridden.

    Returns
    -------
    earthkit.plots.styles.Style
        The instantiated style object.

    Raises
    ------
    KeyError
        If no style with the given name is found in any registered style
        library.

    Examples
    --------
    >>> import earthkit.plots
    >>> style = earthkit.plots.styles.load_style("temperature-2m-turbo-celsius")
    >>> chart.contourf(data, style=style)
    """
    style_dict = _cache.get_named_style(name)
    if style_dict is not None:
        return styles.Style.from_dict({**style_dict, **kwargs})
    raise KeyError(f"No style named {name!r}. Available styles: {list_styles()}")


def list_styles() -> list[str]:
    """
    Return a sorted list of all available named style names.

    These names can be passed to :func:`load_style` or used directly as the
    ``style`` parameter in any plotting method.

    Returns
    -------
    list of str

    Examples
    --------
    >>> import earthkit.plots
    >>> earthkit.plots.list_styles()
    ['mslp-contour-hpa', 'mslp-contour-pa', 'precipitation-turbo-kg-m2', ...]
    """
    return _cache.list_named_styles()
