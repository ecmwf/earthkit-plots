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

import glob
import os
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

import yaml

from earthkit.plots import styles
from earthkit.plots._plugins import PLUGINS
from earthkit.plots.metadata.units import are_equal
from earthkit.plots.schemas import schema

METADATA = dict[str, Any | Sequence[Any]]


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

    if schema.style_library not in PLUGINS:
        path = Path(schema.style_library).expanduser()
        identities_path = path / "identities"
        styles_path = path / "auto-styles"
    else:
        identities_path = PLUGINS[schema.style_library]["identities"]
        styles_path = PLUGINS[schema.style_library]["styles"]

    identity = None

    for fname in glob.glob(str(identities_path / "*")):
        if os.path.isfile(fname):
            with open(fname) as f:
                config = yaml.load(f, Loader=yaml.SafeLoader)
        else:
            continue

        if any(criteria_matches(data, c) for c in config["criteria"]):
            identity = config["id"]
            break
    else:
        return styles.DEFAULT_STYLE

    for fname in glob.glob(str(styles_path / "*")):
        if os.path.isfile(fname):
            with open(fname) as f:
                style_config = yaml.load(f, Loader=yaml.SafeLoader)
        else:
            continue
        if style_config["id"] == identity:
            break
    else:
        return styles.DEFAULT_STYLE

    if schema.use_preferred_units:
        style = style_config["styles"][style_config["optimal"]]
    else:
        for _, style in style_config["styles"].items():
            if are_equal(style.get("units"), units):
                break
        else:
            # No style matching units found — try matching source units, or
            # fall back to any style without explicit units
            for _, style in style_config["styles"].items():
                if are_equal(style.get("units"), source_units):
                    break
            else:
                for _, style in style_config["styles"].items():
                    if "units" not in style:
                        break
                else:
                    return styles.DEFAULT_STYLE

    # If the caller requested a specific target units that differs from the
    # style variant's units, override the style units so the colorbar label
    # reflects the actual plotted units (the Source handles the conversion).
    style_units = style.get("units")
    if units is not None and not are_equal(units, style_units):
        kwargs.setdefault("units", units)

    return styles.Style.from_dict({**style, **kwargs})


def _iter_named_styles():
    """
    Yield ``(name, style_dict)`` for every named style variant across all
    registered style libraries.

    Only variants that carry a ``name`` key are yielded.
    """
    seen_paths = set()
    for plugin_paths in PLUGINS.values():
        styles_path = plugin_paths["styles"]
        for fname in sorted(glob.glob(str(styles_path / "*"))):
            if not os.path.isfile(fname) or fname in seen_paths:
                continue
            seen_paths.add(fname)
            with open(fname) as f:
                config = yaml.load(f, Loader=yaml.SafeLoader)
            for style_dict in config.get("styles", {}).values():
                name = style_dict.get("name")
                if name:
                    yield name, style_dict


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
    for style_name, style_dict in _iter_named_styles():
        if style_name == name:
            return styles.Style.from_dict({**style_dict, **kwargs})
    available = list_styles()
    raise KeyError(f"No style named {name!r}. " f"Available styles: {available}")


def list_styles():
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
    >>> earthkit.plots.styles.list_styles()
    ['mslp-contour-hpa', 'mslp-contour-pa', 'precipitation-turbo-kg-m2', ...]
    """
    return sorted(name for name, _ in _iter_named_styles())
