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

from earthkit.plots.components.figures import Figure
from earthkit.plots.metadata.formatters import LayerFormatter
from earthkit.plots.metadata.units import are_equal
from earthkit.plots.temporal.timeseries import TimeSeries

CLASS_KWARGS = {
    "size",
}


def _apply_ticks(subplot, xticks, yticks):
    """Apply xticks/yticks configuration to a subplot."""
    if xticks is not None:
        if isinstance(xticks, str):
            subplot.xticks(frequency=xticks)
        else:
            subplot.xticks(**xticks)
    if yticks is not None:
        if isinstance(yticks, str):
            subplot.yticks(frequency=yticks)
        else:
            subplot.yticks(**yticks)


def timeseries(
    data,
    *args,
    overlay=False,
    groupby=None,
    rows=None,
    columns=None,
    title=None,
    subplot_titles="{variable_name}",
    xticks=None,
    yticks=None,
    xlabel=None,
    ylabel=None,
    plot="line",
    **kwargs,
):
    """
    Create a time series plot with automatic configuration.

    This is a convenience function that creates a TimeSeries subplot (or a
    Figure of multiple TimeSeries subplots) with sensible defaults for time
    series visualization.

    When *data* is an xarray Dataset with more than one data variable, a
    separate subplot is created for each variable by default (one per row).
    Pass ``overlay=True`` to plot all variables on a single subplot instead.
    Use ``groupby`` to split each variable further along a coordinate dimension
    (produces a variable × group grid).

    .. warning::
        This function uses the experimental TimeSeries class. We welcome
        feedback and bug reports on GitHub issues:
        https://github.com/ecmwf/earthkit-plots/issues

    Parameters
    ----------
    data : array-like, xarray DataArray/Dataset, or earthkit data source
        The time series data to plot.
    *args : tuple
        Additional positional arguments passed to the plotting method.
    overlay : bool, optional
        When *data* is a multi-variable Dataset, plot all variables on a single
        subplot instead of creating one subplot per variable. Default is False.
    groupby : str, optional
        Coordinate name along which to split each variable into separate
        columns (e.g. ``"step"`` or ``"number"``).  Only used when *data* is
        a multi-variable Dataset and *overlay* is False.
    rows : int, optional
        Override the number of rows in the Figure layout.  Only used in the
        multi-panel path.
    columns : int, optional
        Override the number of columns in the Figure layout.  Only used in the
        multi-panel path.
    title : str, optional
        Figure-level title.  In the single-panel path this is the subplot
        title.  Supports format strings like ``{variable_name}``.
        Default is ``None`` (no title).
    subplot_titles : str, optional
        Per-panel title format string.  Ignored when ``overlay=True`` or when
        there is only a single panel.  Default is ``"{variable_name}"``.
    xticks : str or dict, optional
        Configuration for x-axis ticks. If a string, treated as frequency
        (e.g. ``"Y"``, ``"M6"``, ``"D7"``, ``"h"``). If a dict, passed as
        kwargs to ``xticks()``. Default is None (automatic).
    yticks : str or dict, optional
        Configuration for y-axis ticks.  Same format as *xticks*.
        Default is None (automatic).
    xlabel : str, optional
        Label for the x-axis. Default is None (automatic).
    ylabel : str, optional
        Label for the y-axis. Default is None (automatic).
    plot : str, optional
        Plotting method to call on each TimeSeries subplot.  Options include
        ``"line"``, ``"scatter"``, ``"bar"``, etc. Default is ``"line"``.
    **kwargs : dict
        Additional keyword arguments passed to the plotting method and (in the
        single-panel path) to the TimeSeries constructor.  Special kwargs:

        - ``size`` : tuple – Figure size as ``(width, height)`` in inches.
          Default is ``(8, 4)`` per subplot.

    Returns
    -------
    TimeSeries or Figure
        A :class:`~earthkit.plots.temporal.timeseries.TimeSeries` subplot when
        a single panel is produced, or a
        :class:`~earthkit.plots.components.figures.Figure` when multiple panels
        are created.

    Examples
    --------
    Single variable – unchanged behaviour:

    >>> ts = timeseries(ds["t2m"])
    >>> ts.show()

    Multi-variable Dataset – one row per variable:

    >>> fig = timeseries(ds)
    >>> fig.show()

    Multi-variable Dataset with groupby – variable × group grid:

    >>> fig = timeseries(ds, groupby="step")
    >>> fig.show()

    Overlay all variables on one subplot:

    >>> ts = timeseries(ds, overlay=True)
    >>> ts.show()

    Custom subplot titles:

    >>> fig = timeseries(ds, subplot_titles="{variable_name} [{units}]")
    >>> fig.show()

    Bar chart instead of line:

    >>> fig = timeseries(ds, plot="bar")
    >>> fig.show()
    """
    import xarray as xr

    # ------------------------------------------------------------------ #
    # Multi-panel path: multi-variable Dataset, overlay=False             #
    # Delegates to Figure.timeseries() which is the canonical engine.     #
    # ------------------------------------------------------------------ #
    if not overlay and isinstance(data, xr.Dataset) and len(data.data_vars) > 1:
        size = kwargs.pop("size", None)
        # groupby=None → row="variable" (default); groupby set → col=groupby
        col = groupby if groupby is not None else None
        fig = Figure()
        fig.timeseries(
            data,
            *args,
            row="variable",
            col=col,
            plot=plot,
            subplot_titles=subplot_titles,
            rows=rows,
            columns=columns,
            size=size,
            xticks=xticks,
            yticks=yticks,
            xlabel=xlabel,
            ylabel=ylabel,
            **kwargs,
        )
        if title:
            try:
                fig.title(title)
            except Exception:
                pass
        return fig

    # ------------------------------------------------------------------ #
    # Overlay path: multi-variable Dataset, overlay=True                  #
    # ------------------------------------------------------------------ #
    if overlay and isinstance(data, xr.Dataset) and len(data.data_vars) > 1:
        class_kwargs = {
            kwarg: kwargs.pop(kwarg) for kwarg in CLASS_KWARGS if kwarg in kwargs
        }
        ts = TimeSeries(**class_kwargs)

        # Track axes by units string so variables sharing units share an axis.
        # axes_by_units: units_str -> matplotlib Axes
        # layers_by_ax:  matplotlib Axes -> list of layers (for ylabel labelling)
        axes_by_units = {}
        layers_by_ax = {}
        primary_ax = None

        for var_name in data.data_vars:
            da = data[var_name]
            var_units = da.attrs.get("units", None)

            if not axes_by_units:
                # First variable — plot on the primary axis
                layers_before = len(ts.layers)
                getattr(ts, plot)(da, *args, **kwargs)
                primary_ax = ts._ax
                axes_by_units[var_units] = primary_ax
                layers_by_ax[primary_ax] = ts.layers[layers_before:]
            else:
                # Find a compatible existing axis, or create a twinx
                target_ax = None
                for existing_units, existing_ax in axes_by_units.items():
                    if are_equal(var_units, existing_units):
                        target_ax = existing_ax
                        break

                if target_ax is None:
                    target_ax = primary_ax.twinx()
                    axes_by_units[var_units] = target_ax
                    layers_by_ax[target_ax] = []

                # Temporarily redirect ts._ax so the plot method draws on target_ax
                original_ax = ts._ax
                ts._ax = target_ax
                layers_before = len(ts.layers)
                getattr(ts, plot)(da, *args, **kwargs)
                ts._ax = original_ax
                layers_by_ax[target_ax].extend(ts.layers[layers_before:])

        ts.xlabel(xlabel)
        _apply_ticks(ts, xticks, yticks)

        # Set ylabel on each axis from its own layers' metadata
        for ax, ax_layers in layers_by_ax.items():
            if ylabel is not None:
                ax.set_ylabel(ylabel)
            elif ax_layers:
                try:
                    src = ax_layers[0].sources[0]
                    units = src.y.metadata("units")
                    lbl = "{variable_name} ({units})" if units else "{variable_name}"
                    ax.set_ylabel(LayerFormatter(ax_layers[0]).format(lbl))
                except Exception:
                    pass

        if title:
            ts.title(title)
        return ts

    # ------------------------------------------------------------------ #
    # Single-panel path: DataArray, single-variable Dataset, or non-xarray #
    # ------------------------------------------------------------------ #
    class_kwargs = {
        kwarg: kwargs.pop(kwarg) for kwarg in CLASS_KWARGS if kwarg in kwargs
    }
    ts = TimeSeries(**class_kwargs)
    getattr(ts, plot)(data, *args, **kwargs)
    ts.xlabel(xlabel)
    ts.ylabel(ylabel)
    _apply_ticks(ts, xticks, yticks)
    if title:
        ts.title(title)
    return ts
