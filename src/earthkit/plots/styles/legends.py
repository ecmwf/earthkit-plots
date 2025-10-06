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

import matplotlib.colors as mcolors
import numpy as np
from matplotlib.patches import Patch

DEFAULT_LEGEND_LABEL = "{variable_name} ({units})"

_DISJOINT_LEGEND_LOCATIONS = {
    "bottom": {
        "loc": "upper center",
        "bbox_to_anchor": (0.5, -0.05),
    },
    "top": {
        "loc": "lower center",
        "bbox_to_anchor": (0.5, 1.0),
    },
    "left": {
        "loc": "upper right",
        "bbox_to_anchor": (-0.05, 1.0),
    },
    "right": {
        "loc": "upper left",
        "bbox_to_anchor": (1.05, 1.0),
    },
    "top left": {
        "loc": "lower center",
        "bbox_to_anchor": (0.25, 1),
    },
    "top right": {
        "loc": "lower center",
        "bbox_to_anchor": (0.75, 1),
    },
}


def colorbar(layer, *args, ax=None, color="black", **kwargs):
    """
    Produce a colorbar for a given layer.

    Parameters
    ----------
    layer : earthkit.maps.charts.layers.Layer
        The layer for which to produce a colorbar.
    **kwargs
        Any keyword arguments accepted by `matplotlib.figures.Figure.colorbar`.
    """
    label = kwargs.pop("label", None)
    if label is None:
        label = layer.format_string(
            DEFAULT_LEGEND_LABEL, default="", issue_warnings=False
        )
    else:
        label = layer.format_string(label)

    shrink: float = kwargs.pop("shrink", 0.8)
    aspect: int = kwargs.pop("aspect", 35)

    kwargs = {**layer.style._legend_kwargs, **kwargs}
    kwargs.setdefault("format", lambda x, _: f"{x:g}")

    if ax is None:
        kwargs["ax"] = layer.axes
    else:
        kwargs["cax"] = ax

    cbar = layer.fig.colorbar(
        layer.mappable,
        *args,
        label=label,
        shrink=shrink,
        aspect=aspect,
        **kwargs,
    )
    cbar.ax.minorticks_off()
    cbar.ax.tick_params(size=0, color=color)

    if cbar.solids is not None:
        cbar.solids.set(alpha=1)

    return cbar


def disjoint(layer, *args, location="bottom", frameon=False, **kwargs):
    """
    Produce a disjoint legend for a given layer.

    Parameters
    ----------
    layer : earthkit.maps.charts.layers.Layer
        The layer for which to produce a colorbar.
    **kwargs
        Any keyword arguments accepted by `matplotlib.figures.Figure.legend`.
    """
    kwargs.pop("format", None)  # remove higher-level kwargs which are invalid

    label = kwargs.pop("label", "Legend")
    label = layer.format_string(label)

    source = layer.axes[0] if len(layer.axes) == 1 else layer.fig
    location_kwargs = _DISJOINT_LEGEND_LOCATIONS.get(location, {})

    # Check if the mappable is from contourf (which has legend_elements)
    if hasattr(layer.mappable, "legend_elements"):
        artists, labels = layer.mappable.legend_elements()
        for artist in artists:
            if isinstance(artist, Patch):
                artist.set(linewidth=0.5, edgecolor="#555")
    else:
        cmap = layer.mappable.get_cmap()
        norm = layer.mappable.norm

        # Try to extract boundaries directly
        if isinstance(norm, mcolors.BoundaryNorm):
            levels = norm.boundaries  # Correct method for unevenly spaced levels
        elif hasattr(layer.mappable, "colorbar") and hasattr(
            layer.mappable.colorbar, "boundaries"
        ):
            levels = layer.mappable.colorbar.boundaries  # Backup if available
        else:
            levels = np.linspace(
                norm.vmin, norm.vmax, cmap.N
            )  # Fallback, but not ideal

        # Generate color patches manually
        artists = [
            Patch(facecolor=cmap(norm(level)), edgecolor="#555", linewidth=0.5)
            for level in levels
        ]

    labels = kwargs.pop("labels", layer.style._bin_labels) or labels

    kwargs["ncols"] = kwargs.get(
        "ncols", estimate_legend_cols(layer.axes, labels, position=location)
    )

    legend = source.legend(
        artists,
        labels,
        *args,
        title=label,
        frameon=frameon,
        **{**location_kwargs, **kwargs},
    )

    # Matplotlib removes previous legends, so manually re-add them
    if hasattr(layer.fig, "_previous_legend"):
        layer.fig.add_artist(layer.fig._previous_legend)
    layer.fig._previous_legend = legend

    return legend


def vector(layer, *args, vector_reference=16, **kwargs):
    layer.axes[-1].quiverkey(
        layer.mappable,
        1,
        1.02,
        vector_reference,
        label=f"{vector_reference} {layer.style.units or '$m s^{-1}$'}",
    )
    uses_cbar = getattr(layer.mappable, "_colorbar", True)
    cbar = None
    if uses_cbar:
        cbar = colorbar(layer, *args, **kwargs)
    return cbar


def estimate_legend_cols(axes, labels, position="top"):
    """
    Estimates the number of columns for a legend based on the total width or height of a list of axes,
    the position of the legend, and the lengths of the labels.

    Args:
    axes (list of matplotlib.axes.Axes): The list of axes objects to which the legend will be aligned.
    labels (list of str): The labels for the legend.
    position (str): Position of the legend, choices are 'top', 'bottom', 'left', 'right'.

    Returns:
    int: Estimated number of columns for the legend.
    """
    # Constants for character width in pixels and padding
    char_width = 6  # rough estimate of character width in pixels
    padding = 40  # additional padding around labels in pixels

    # Calculate total width of each label
    label_widths = [len(label) * char_width + padding for label in labels]

    if position in ["top", "bottom"]:
        # Calculate the total width of all axes
        total_width = sum(ax.get_position().width for ax in axes)
        available_width = (
            total_width * axes[0].figure.get_figwidth() * axes[0].figure.dpi
        )
    else:  # 'left', 'right'
        # Calculate the total height of all axes
        total_height = sum(ax.get_position().height for ax in axes)
        available_width = (
            total_height * axes[0].figure.get_figheight() * axes[0].figure.dpi
        )

    # Sum of label widths
    total_label_width = np.sum(label_widths)

    # Calculate the number of columns that would fit
    num_columns = max(1, int(available_width / total_label_width * len(labels)))

    return num_columns
