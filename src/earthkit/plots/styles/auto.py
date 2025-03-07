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

import yaml

from earthkit.plots import styles
from earthkit.plots.metadata.units import are_equal
from earthkit.plots.schemas import schema


def _get_style_library_path(subfolder):
    subfolder_paths = []
    for plugin in schema._plugins:
        subfolder_paths.append(plugin[subfolder])
    return subfolder_paths


# TODO: add cache for style guessing
def _find_identity(data):

    plugin_paths = _get_style_library_path("identities")

    identity = None
    for identities_path in plugin_paths:  # loop through all the plugins
        for fname in glob.glob(str(identities_path / "*")):

            if os.path.isfile(fname):
                with open(fname, "r") as f:
                    config = yaml.load(f, Loader=yaml.SafeLoader)
            else:
                continue

            for criteria in config["criteria"]:
                for key, value in criteria.items():
                    if data.metadata(key, default=None) == value:
                        identity = config["id"]
                        break
                else:
                    continue
                break
            else:
                continue
            break
    return identity


# TODO: add cache for style guessing
def _find_style_config(identity=None):

    plugin_paths = _get_style_library_path("styles")

    style_config = None
    for styles_path in plugin_paths:  # loop through all the plugins
        for fname in glob.glob(str(styles_path / "*")):

            if os.path.isfile(fname):
                with open(fname, "r") as f:
                    style_config = yaml.load(f, Loader=yaml.SafeLoader)
            else:
                continue

            if identity is None and style_config.get("id") is None:
                break

            if style_config.get("id") == identity:
                break

    return style_config


def _style_from_units(style_config, units):
    optimal_style = style_config["styles"][style_config["optimal"]]
    if schema.use_preferred_units:
        style = optimal_style
    else:
        for _, style in style_config["styles"].items():
            if are_equal(style.get("units"), units):
                break
        else:
            style = optimal_style
    return style


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

    if not schema.automatic_styles or schema.style_library is None:
        return styles.DEFAULT_STYLE

    # first loop identity files within the identities folder in the style library
    identity = _find_identity(data)
    if identity is None:
        return styles.DEFAULT_STYLE

    # from identity, find the style configuration file
    style_config = _find_style_config(identity)
    if style_config is None:
        return styles.DEFAULT_STYLE

    # choose best style from units
    if units is None:
        units = data.units
    style = _style_from_units(style_config, units)

    return styles.Style.from_dict({**style, **kwargs})


def get_available_styles(data):
    """
    Get the available styles for the data based on its metadata.

    The styles are determined by the identity of the data, which is matched
    against the identities in the style library. If the style library is not
    set or no identity matches the metadata, the default style is returned.

    Parameters
    ----------
    data : earthkit.plots.sources.Source
        The data object containing the metadata.
    """

    styles = []

    for field in data:

        # first loop identity files within the identities folder in the style library
        identity = _find_identity(field)

        if identity is None:
            return get_common_styles()

        # from identity, find the style configuration file
        style_config = _find_style_config(identity)

        styles.append(style_config["styles"])

    return styles


def get_common_styles():
    """
    Get the common styles (styles without id).
    """
    styles = None
    style_config = _find_style_config()
    if style_config is None:
        styles = {"default": styles.DEFAULT_STYLE}
    else:
        styles = style_config.get("styles")
        if styles is None:
            styles = {"default": styles.DEFAULT_STYLE}

    return styles
