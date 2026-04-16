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

"""Utilities for removing data-layer artists from matplotlib axes.

Ancillary artists (coastlines, gridlines, borders, etc.) are added directly
to axes via cartopy's ``add_feature()`` and are never stored in
``subplot.layers``, so removing only the layer list leaves them untouched.
"""


def _remove_mappable(mappable):
    """Remove a single matplotlib artist or collection from its axes.

    Parameters
    ----------
    mappable : matplotlib artist
        The artist to remove.  ContourSets are handled via their
        ``.collections`` attribute; everything else via ``.remove()``.
    """
    if hasattr(mappable, "collections"):
        for collection in mappable.collections:
            try:
                collection.remove()
            except ValueError:
                pass
    elif hasattr(mappable, "remove"):
        try:
            mappable.remove()
        except ValueError:
            pass


def remove_data_layers(subplot):
    """Remove all data-layer artists from *subplot* and clear its layer list.

    Static ancillary features (coastlines, borders, gridlines) and colorbars
    on separate axes are left untouched.

    Parameters
    ----------
    subplot : earthkit.plots.components.subplots.Subplot
        The subplot whose data layers should be cleared.
    """
    for layer in subplot.layers:
        _remove_mappable(layer.mappable)
    subplot.layers.clear()
