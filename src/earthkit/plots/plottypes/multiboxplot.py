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

"""
Multiboxplot (letter-value plot) rendering.

This module contains the pure rendering logic for multiboxplot and its
companion legend.  Both functions are deliberately free of Subplot/Figure
state — they only require a matplotlib Axes and the prepared data, so they
can be tested without a display and reused outside the Subplot API.

The public interface for users remains on ``Subplot`` (thin wrappers that
handle unit resolution, Source construction, and Layer bookkeeping).
"""

from __future__ import annotations

from typing import NamedTuple

import numpy as np


class MultiboxplotResult(NamedTuple):
    """
    Data returned by :func:`draw_multiboxplot`.

    Carries everything that :func:`draw_multiboxplot_legend` needs, replacing
    the ad-hoc ``layer._multiboxplot_*`` attribute protocol.

    Attributes
    ----------
    mappables : list
        Matplotlib artists produced (one whisker line + one box per quantile
        pair, plus the median line).  The first element is used as the legend
        proxy artist.
    quantiles : list[float]
        Quantile values used (e.g. ``[0, 0.1, 0.25, 0.5, 0.75, 0.9, 1]``).
    color : str or tuple
        Base fill color of the innermost box.
    styling : dict
        Resolved drawing properties so the legend can reproduce the same
        appearance without having access to the original ``*props`` dicts.
        Keys: ``whisker_color``, ``whisker_linewidth``, ``box_edgecolor``,
        ``box_linewidth``, ``median_color``, ``median_linewidth``.
    quantile_data : xarray.DataArray
        The quantile-reduced DataArray (shape: ``(n_quantiles, n_x)``), used
        by the Subplot wrapper to build the representative Source for the Layer.
    quantile_dim : str
        Name of the quantile dimension in *quantile_data*.
    """

    mappables: list
    quantiles: list
    color: object
    styling: dict
    quantile_data: object  # xarray.DataArray — avoid hard import at module level
    quantile_dim: str


def _darken_color(color, factor: float = 0.25):
    """Return a darker version of *color* by scaling RGB channels."""
    from matplotlib.colors import to_hex, to_rgb

    rgb = to_rgb(color)
    return to_hex(tuple(c * factor for c in rgb))


def _resolve_quantiles(data, quantiles, dim):
    """
    Validate inputs and compute (or validate) the quantile-reduced DataArray.

    Returns
    -------
    (quantile_data, quantile_dim, q_list, x_dim)
    """

    if quantiles is None:
        # Caller asserts data already holds pre-computed quantile values.
        if dim is None:
            raise ValueError(
                "When quantiles=None (pre-computed), 'dim' must name the "
                "dimension that holds the quantile values."
            )
        if dim not in data.dims:
            raise ValueError(
                f"Dimension '{dim}' not found; available: {list(data.dims)}"
            )
        quantile_data = data
        quantile_dim = dim
        q_list = (
            sorted(data.coords[dim].values.tolist())
            if dim in data.coords
            else list(range(data.sizes[dim]))
        )
    else:
        if quantiles == "auto":
            quantiles = [0, 0.1, 0.25, 0.5, 0.75, 0.9, 1]
        quantiles = sorted(quantiles)
        if not all(0.0 <= q <= 1.0 for q in quantiles):
            raise ValueError("All quantiles must be between 0 and 1.")
        if data.ndim < 2:
            raise ValueError(
                f"Data must have at least 2 dimensions for multiboxplot (got {list(data.dims)})."
            )
        if dim is None:
            dim = data.dims[0]
        elif dim not in data.dims:
            raise ValueError(
                f"Dimension '{dim}' not found; available: {list(data.dims)}"
            )

        # Preserve attrs through quantile reduction — xarray drops them by default.
        attrs_backup = data.attrs.copy()
        coord_attrs_backup = {c: data.coords[c].attrs.copy() for c in data.coords}
        quantile_data = data.quantile(quantiles, dim=dim)
        quantile_dim = "quantile"
        q_list = quantiles
        quantile_data.attrs.update(attrs_backup)
        for coord, attrs in coord_attrs_backup.items():
            if coord in quantile_data.coords:
                quantile_data.coords[coord].attrs.update(attrs)

    remaining = [d for d in quantile_data.dims if d != quantile_dim]
    if len(remaining) != 1:
        raise ValueError(
            f"After quantile processing, expected 1 remaining dimension, got {remaining}."
        )
    x_dim = remaining[0]
    return quantile_data, quantile_dim, q_list, x_dim


def _apply_unit_conversion(data, dim, target_yunits):
    """
    Return a copy of *data* with y-values converted to *target_yunits*.

    Uses a linear scale+offset derived from two representative points so that
    the conversion is correct for affine unit relationships (e.g. K → °C).
    When the conversion makes no numeric change (same units), returns *data*
    unchanged.
    """
    import xarray as xr

    from earthkit.plots.sources import get_source
    from earthkit.plots.sources.context import PlotContext

    data_slice = data.isel({dim: 0})
    src_original = get_source(data_slice, context=PlotContext.CARTESIAN_1D)
    src_converted = get_source(
        data_slice, context=PlotContext.CARTESIAN_1D, units=target_yunits
    )
    original = src_original.y.values
    converted = src_converted.y.values

    if np.array_equal(original, converted) or len(original) < 2:
        return data

    scale = (converted[1] - converted[0]) / (original[1] - original[0])
    offset = converted[0] - scale * original[0]

    attrs = data.attrs.copy()
    coord_attrs = {c: data.coords[c].attrs.copy() for c in data.coords}
    result = xr.DataArray(
        data.values * scale + offset,
        dims=data.dims,
        coords=data.coords,
        attrs=attrs,
    )
    for coord, ca in coord_attrs.items():
        if coord in result.coords:
            result.coords[coord].attrs.update(ca)
    return result


def _resolve_box_styling(
    color, ax, boxprops, whiskerprops, medianprops, showcaps, capprops
):
    """
    Resolve all drawing properties from the user-supplied ``*props`` dicts.

    Returns a flat dict of every resolved property so the caller does not need
    to repeat this logic in the legend.
    """
    boxprops = boxprops or {}
    box_edgecolor = boxprops.get("edgecolor", "black")
    box_linewidth = boxprops.get("linewidth", 1.0)
    box_linestyle = boxprops.get("linestyle", "solid")

    if color is None:
        color = ax._get_lines.get_next_color()

    whiskerprops = whiskerprops or {}
    whisker_color = whiskerprops.get("color", box_edgecolor)
    whisker_linewidth = whiskerprops.get("linewidth", box_linewidth)
    whisker_linestyle = whiskerprops.get("linestyle", "solid")

    medianprops = medianprops or {}
    median_color = medianprops.get("color", _darken_color(color, 0.25))
    median_linewidth = medianprops.get("linewidth", 1.5)
    median_linestyle = medianprops.get("linestyle", "solid")
    median_alpha = medianprops.get("alpha", 1.0)

    cap_props = {}
    if showcaps:
        capprops = capprops or {}
        cap_props = {
            "color": capprops.get("color", whisker_color),
            "linewidth": capprops.get("linewidth", whisker_linewidth),
            "linestyle": capprops.get("linestyle", "solid"),
            "width_factor": capprops.get("capwidth", 1.0),
        }

    return {
        "color": color,
        "box_edgecolor": box_edgecolor,
        "box_linewidth": box_linewidth,
        "box_linestyle": box_linestyle,
        "whisker_color": whisker_color,
        "whisker_linewidth": whisker_linewidth,
        "whisker_linestyle": whisker_linestyle,
        "median_color": median_color,
        "median_linewidth": median_linewidth,
        "median_linestyle": median_linestyle,
        "median_alpha": median_alpha,
        "cap_props": cap_props,
    }


def _compute_x_spacing(x_values):
    """Return (is_datetime, base_box_width) from the x coordinate array."""
    is_datetime = np.issubdtype(x_values.dtype, np.datetime64)

    if len(x_values) > 1:
        if is_datetime:
            from matplotlib.dates import date2num

            x_num = date2num(x_values)
            spacing = float(np.min(np.diff(x_num)))
        else:
            spacing = float(np.min(np.diff(x_values.astype(float))))
    else:
        spacing = 1.0

    return is_datetime, 0.6 * spacing


def _to_x_pos(x_val, is_datetime):
    """Convert a single x value to a matplotlib numeric position."""
    if is_datetime:
        from matplotlib.dates import date2num

        return date2num(x_val)
    return float(x_val)


def draw_multiboxplot(
    ax,
    data,
    *,
    x="auto",
    dim=None,
    quantiles="auto",
    color=None,
    target_yunits=None,
    boxprops=None,
    whiskerprops=None,
    medianprops=None,
    capprops=None,
    showcaps=False,
) -> MultiboxplotResult:
    """
    Draw a multiboxplot (letter-value plot) onto *ax*.

    Visualises quantiles as stacked boxes with varying widths.  The outermost
    pair is rendered as a whisker line; inner pairs as progressively lighter
    and narrower filled rectangles; the median (if present) as a horizontal
    line.

    This function is free of ``Subplot`` state — it only requires a matplotlib
    Axes.  Unit conversion must be applied to *data* **before** calling this
    function; use :func:`_apply_unit_conversion` if needed.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The target axes.
    data : xarray.DataArray
        Input data.  Must have at least two dimensions (one ensemble/quantile
        dimension and one x dimension) unless *quantiles* is ``None``.
    x : str, optional
        Dimension name for the x-axis.  ``"auto"`` uses the remaining
        dimension after the quantile dimension is removed.
    dim : str, optional
        Dimension along which to compute quantiles.  If ``None``, the
        left-most dimension is used.  When *quantiles* is ``None``, this
        names the pre-computed quantile dimension.
    quantiles : list[float], "auto", or None, optional
        ``"auto"`` → ``[0, 0.1, 0.25, 0.5, 0.75, 0.9, 1]``.
        A list → compute those quantiles.
        ``None`` → treat *dim* as a pre-computed quantile dimension.
    color : str or tuple, optional
        Base fill colour.  Defaults to the next colour in the axes cycle.
    target_yunits : str, optional
        If provided, apply unit conversion to *data* before quantile
        reduction using :func:`_apply_unit_conversion`.
    boxprops, whiskerprops, medianprops, capprops : dict, optional
        Drawing properties forwarded from the user.
    showcaps : bool, optional
        Whether to draw horizontal cap lines at whisker ends.

    Returns
    -------
    MultiboxplotResult
        Named tuple with ``mappables``, ``quantiles``, ``color``,
        ``styling``, ``quantile_data``, and ``quantile_dim``.
    """
    import xarray as xr
    from matplotlib.colors import to_rgb
    from matplotlib.patches import Rectangle

    # Unwrap single-variable Datasets.
    if isinstance(data, xr.Dataset):
        data_vars = [v for v in data.data_vars if data[v].ndim > 0]
        if len(data_vars) != 1:
            raise ValueError(
                f"Dataset must have exactly one non-scalar variable; got {data_vars}"
            )
        data = data[data_vars[0]]

    data = data.squeeze()

    # Apply unit conversion before quantile reduction so box positions are in
    # the target units.  Skip when quantiles=None because the data is already
    # pre-computed — converting would produce nonsensical position values.
    if target_yunits is not None and quantiles is not None:
        reduce_dim = (
            dim if dim is not None else (data.dims[0] if data.ndim >= 2 else None)
        )
        if reduce_dim is not None:
            data = _apply_unit_conversion(data, reduce_dim, target_yunits)

    quantile_data, quantile_dim, q_list, x_dim = _resolve_quantiles(
        data, quantiles, dim
    )

    x_values = quantile_data[x_dim].values
    q_values = quantile_data.values  # shape: (n_quantiles, n_x)

    # Pair quantiles symmetrically: (0th, last), (1st, second-to-last), …
    n_q = len(q_list)
    pairs = [(i, n_q - 1 - i) for i in range(n_q // 2)]
    median_idx = n_q // 2 if n_q % 2 == 1 else None

    props = _resolve_box_styling(
        color, ax, boxprops, whiskerprops, medianprops, showcaps, capprops
    )
    plot_color = props["color"]
    rgb = to_rgb(plot_color)

    is_datetime, base_width = _compute_x_spacing(x_values)

    # Register the x-axis as a date axis before drawing any patches or lines
    # with numeric (date2num) coordinates.  Without this, matplotlib never
    # installs the date converter and the x-axis shows raw floats.
    if is_datetime:
        ax.plot([], [], visible=False)
        ax.xaxis.update_units(x_values)

    mappables = []

    for x_idx, x_val in enumerate(x_values):
        xp = _to_x_pos(x_val, is_datetime)

        for pair_idx, (lo_i, hi_i) in enumerate(pairs):
            width_factor = (pair_idx + 1) / len(pairs)
            box_width = base_width * width_factor
            y_lo = float(q_values[lo_i, x_idx])
            y_hi = float(q_values[hi_i, x_idx])

            if pair_idx == 0:
                # Outermost pair → whisker line
                line = ax.plot(
                    [xp, xp],
                    [y_lo, y_hi],
                    color=props["whisker_color"],
                    linewidth=props["whisker_linewidth"],
                    linestyle=props["whisker_linestyle"],
                    zorder=3,
                )
                if x_idx == 0:
                    mappables.extend(line)

                if showcaps:
                    hw = base_width * props["cap_props"]["width_factor"] / 2
                    for y_cap in (y_lo, y_hi):
                        ax.plot(
                            [xp - hw, xp + hw],
                            [y_cap, y_cap],
                            color=props["cap_props"]["color"],
                            linewidth=props["cap_props"]["linewidth"],
                            linestyle=props["cap_props"]["linestyle"],
                            zorder=3,
                        )
            else:
                # Inner pairs → filled rectangles, darkening toward the centre
                norm_i = (pair_idx - 1) / max(1, len(pairs) - 2)
                lightness = 0.4 * (1.0 - norm_i)
                box_color = tuple(c * (1 - lightness) + lightness for c in rgb)

                rect = Rectangle(
                    (xp - box_width / 2, y_lo),
                    box_width,
                    y_hi - y_lo,
                    facecolor=box_color,
                    edgecolor=props["box_edgecolor"],
                    linewidth=props["box_linewidth"],
                    linestyle=props["box_linestyle"],
                    zorder=4,
                )
                ax.add_patch(rect)
                if x_idx == 0 and pair_idx == 1:
                    mappables.append(rect)

        # Median line
        if median_idx is not None:
            y_med = float(q_values[median_idx, x_idx])
            mw = base_width * 0.95
            med_line = ax.plot(
                [xp - mw / 2, xp + mw / 2],
                [y_med, y_med],
                color=props["median_color"],
                linewidth=props["median_linewidth"],
                linestyle=props["median_linestyle"],
                alpha=props["median_alpha"],
                zorder=5,
            )
            if x_idx == 0:
                mappables.extend(med_line)

    # Set x limits to include a half-box margin on each side.
    if is_datetime:
        from matplotlib.dates import date2num

        x_num = date2num(x_values)
        ax.set_xlim(x_num[0] - base_width, x_num[-1] + base_width)
    else:
        xf = x_values.astype(float)
        ax.set_xlim(float(xf[0]) - base_width, float(xf[-1]) + base_width)
    ax.autoscale_view(scalex=False, scaley=True)

    styling = {
        "whisker_color": props["whisker_color"],
        "whisker_linewidth": props["whisker_linewidth"],
        "box_edgecolor": props["box_edgecolor"],
        "box_linewidth": props["box_linewidth"],
        "median_color": props["median_color"],
        "median_linewidth": props["median_linewidth"],
    }

    return MultiboxplotResult(
        mappables=mappables,
        quantiles=q_list,
        color=plot_color,
        styling=styling,
        quantile_data=quantile_data,
        quantile_dim=quantile_dim,
    )


def draw_multiboxplot_legend(
    ax,
    result: MultiboxplotResult,
    *,
    location="right",
    fontsize=8,
    color=None,
    boxprops=None,
    whiskerprops=None,
    medianprops=None,
    size=0.75,
    pad=0.1,
):
    """
    Draw a miniature legend for a multiboxplot onto a new axes beside *ax*.

    Creates a small replica of the box structure with labelled quantile
    percentages, placed outside the main axes using
    :func:`mpl_toolkits.axes_grid1.make_axes_locatable`.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The main plot axes (not the legend axes).
    result : MultiboxplotResult
        Return value from :func:`draw_multiboxplot`; provides quantiles,
        colour, and styling defaults.
    location : str, optional
        Which side to attach the legend to.
        One of ``'right'`` (default), ``'left'``, ``'top'``, ``'bottom'``.
    fontsize : int, optional
        Font size for quantile labels.  Default ``8``.
    color : str or tuple, optional
        Override the fill colour.  Defaults to ``result.color``.
    boxprops, whiskerprops, medianprops : dict, optional
        Override any resolved styling from ``result.styling``.
    size : float, optional
        Width/height of the legend square in inches.  Default ``0.75``.
    pad : float, optional
        Gap between *ax* and the legend in inches.  Default ``0.1``.

    Returns
    -------
    matplotlib.axes.Axes
        The new axes containing the legend.

    Raises
    ------
    ValueError
        If *location* is not one of the four valid sides.
    """
    from matplotlib.colors import to_rgb
    from matplotlib.patches import Rectangle
    from mpl_toolkits.axes_grid1 import make_axes_locatable

    valid_locations = ("right", "left", "top", "bottom")
    if location not in valid_locations:
        raise ValueError(
            f"Invalid location {location!r}. Choose from: {valid_locations}"
        )

    stored = result.styling
    quantiles = [float(q) for q in result.quantiles]

    base_color = color if color is not None else result.color
    rgb = to_rgb(base_color)

    whiskerprops = whiskerprops or {}
    whisker_color = whiskerprops.get(
        "color", stored.get("whisker_color", (0.3, 0.3, 0.3))
    )
    whisker_linewidth = whiskerprops.get(
        "linewidth", stored.get("whisker_linewidth", 0.8)
    )

    boxprops = boxprops or {}
    box_edgecolor = boxprops.get("edgecolor", stored.get("box_edgecolor", base_color))
    box_linewidth = boxprops.get("linewidth", stored.get("box_linewidth", 0.5))

    medianprops = medianprops or {}
    median_color = medianprops.get(
        "color", stored.get("median_color", tuple(c * 0.6 for c in rgb))
    )
    median_linewidth = medianprops.get("linewidth", stored.get("median_linewidth", 1.5))

    divider = make_axes_locatable(ax)
    legend_ax = divider.append_axes(location, size=size, pad=pad)
    legend_ax.set_aspect("equal", adjustable="box")

    n_q = len(quantiles)
    pairs = [(i, n_q - 1 - i) for i in range(n_q // 2)]
    median_idx = n_q // 2 if n_q % 2 == 1 else None

    x_center = 0.25
    base_width = 0.15

    for pair_idx, (lo_i, hi_i) in enumerate(pairs):
        width_factor = (pair_idx + 1) / len(pairs)
        box_width = base_width * width_factor
        y_lo, y_hi = quantiles[lo_i], quantiles[hi_i]

        if pair_idx == 0:
            legend_ax.plot(
                [x_center, x_center],
                [y_lo, y_hi],
                color=whisker_color,
                linewidth=whisker_linewidth,
                zorder=1,
            )
        else:
            norm_i = (pair_idx - 1) / max(1, len(pairs) - 2)
            lightness = 0.4 * (1.0 - norm_i)
            box_color = tuple(c * (1 - lightness) + lightness for c in rgb)
            legend_ax.add_patch(
                Rectangle(
                    (x_center - box_width / 2, y_lo),
                    box_width,
                    y_hi - y_lo,
                    facecolor=box_color,
                    edgecolor=box_edgecolor,
                    linewidth=box_linewidth,
                    zorder=2,
                )
            )

    if median_idx is not None:
        mw = base_width * 0.95
        legend_ax.plot(
            [x_center - mw / 2, x_center + mw / 2],
            [quantiles[median_idx], quantiles[median_idx]],
            color=median_color,
            linewidth=median_linewidth,
            zorder=10,
        )

    # Quantile labels: map known boundary values to human-readable strings.
    _QUANTILE_LABELS = {0.0: "min", 0.5: "median", 1.0: "max"}
    for q in quantiles:
        label_text = _QUANTILE_LABELS.get(q, f"{int(round(q * 100))}%")
        legend_ax.text(
            0.4, q, label_text, ha="left", va="center", fontsize=fontsize - 1
        )

    legend_ax.set_xlim(0, 1)
    legend_ax.set_ylim(-0.05, 1.05)
    legend_ax.set_xticks([])
    legend_ax.set_yticks([])
    for spine in legend_ax.spines.values():
        spine.set_visible(False)

    return legend_ax
