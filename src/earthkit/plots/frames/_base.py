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

import os
import string

from earthkit.plots.frames._artists import remove_data_layers

# Methods whose first positional argument is a dataset sliced per frame.
DATA_METHODS = frozenset({
    "contourf",
    "contour",
    "pcolormesh",
    "imshow",
    "scatter",
    "grid_cells",
    "grid_points",
    "point_cloud",
    "quiver",
    "barbs",
    "streamplot",
    "quickplot",
})

# Methods rendered once before any data layers (e.g. coastlines, borders).
STATIC_METHODS = frozenset({
    "coastlines",
    "borders",
    "gridlines",
    "ocean",
    "rivers",
    "lakes",
    "countries",
    "states",
    "glaciers",
    "capitals",
    "cities",
    "airports",
    "background",
})

# Methods rendered once after the first frame's data layers exist
# (legend reads layer style/mappable to build the colorbar).
POST_DATA_METHODS = frozenset({"legend"})


def iter_data(data, index, dim=None):
    """Return the *index*-th slice of *data* without loading other slices.

    Parameters
    ----------
    data : earthkit.data.FieldList, xarray.DataArray, xarray.Dataset, or sequence
        The dataset to slice.
    index : int
        The frame index to extract.
    dim : str, optional
        Dimension name to slice along for xarray objects.  When ``None`` the
        first dimension is used (preserving the existing default behaviour).
        Ignored for FieldList and plain sequences.

    Returns
    -------
    single field, DataArray, or element at *index*
    """
    try:
        from earthkit.data import FieldList

        if isinstance(data, FieldList):
            return data[index]
    except ImportError:
        pass

    try:
        import xarray as xr

        if isinstance(data, (xr.DataArray, xr.Dataset)):
            slice_dim = dim if dim is not None else list(data.dims)[0]
            return data.isel({slice_dim: index})
    except ImportError:
        pass

    return data[index]


def n_slices(data, dim=None):
    """Return the total number of slices in *data*.

    Parameters
    ----------
    data : earthkit.data.FieldList, xarray.DataArray, xarray.Dataset, or sequence
        The dataset to measure.
    dim : str, optional
        Dimension name to count along for xarray objects.  When ``None`` the
        first dimension is used (preserving the existing default behaviour).
        Ignored for FieldList and plain sequences.

    Returns
    -------
    int
    """
    try:
        from earthkit.data import FieldList

        if isinstance(data, FieldList):
            return len(data)
    except ImportError:
        pass

    try:
        import xarray as xr

        if isinstance(data, (xr.DataArray, xr.Dataset)):
            slice_dim = dim if dim is not None else list(data.dims)[0]
            return data.sizes[slice_dim]
    except ImportError:
        pass

    return len(data)


def extract_datetimes(data, n, dim=None):
    """Return a list of datetimes, one per frame, or None if unavailable.

    Parameters
    ----------
    data : dataset
        The dataset from which to extract time metadata.
    n : int
        Number of frames.
    dim : str, optional
        Dimension to iterate along for xarray objects.

    Returns
    -------
    list of datetime.datetime or None
    """
    from earthkit.plots.sources import get_source

    datetimes = []
    for i in range(n):
        src = get_source(iter_data(data, i, dim=dim))
        dt_info = src.datetime()
        vt = dt_info.get("valid_time") if dt_info else None
        if vt is None:
            return None
        datetimes.append(vt)
    return datetimes


def has_placeholders(template):
    """Return True if *template* contains any ``{...}`` format placeholders."""
    return any(field is not None for _, field, _, _ in string.Formatter().parse(template))


def slugify_path(path):
    """Replace spaces with underscores in the filename component of *path*."""
    head, tail = os.path.split(path)
    tail = tail.replace(" ", "_")
    return os.path.join(head, tail) if head else tail


class ChartBase:
    """Call-recording proxy base for Batch and Browser.

    Accepts one or more existing ``Subplot`` / ``Map`` objects and intercepts
    plotting calls made on *this* object — not on the subplot directly.  Calls
    are recorded and replayed frame-by-frame during rendering so that the
    subplot is only touched when a frame is actually needed.

    Data plotting methods (``contourf``, ``contour``, …) record the call and
    do **nothing else** — no data is fetched until ``save()`` or ``show()``
    is called.  Static methods (``coastlines``, ``gridlines``, …) and
    post-data methods (``legend``) are also recorded and replayed in the
    correct order relative to each frame's data layers.

    Parameters
    ----------
    subplot : Subplot, Map, or list thereof
        The subplot(s) to drive.  Must already be attached to a Figure.
    """

    def __init__(self, subplot):
        from earthkit.plots.components.subplots import Subplot as _Subplot

        subplots = subplot if isinstance(subplot, list) else [subplot]
        for sp in subplots:
            if not isinstance(sp, _Subplot):
                raise TypeError(
                    f"Expected a Subplot or Map, got {type(sp).__name__!r}. "
                    "Create a Figure and call fig.add_map() or fig.add_subplot() first."
                )

        self._subplots = subplots

        # Each entry: {"kind": "data"|"static"|"post_data", "method": str,
        #              "args": tuple, "kwargs": dict, "dim": str|None}
        self._calls = []

        self._title_template = None
        self._title_kwargs = {}

    # ------------------------------------------------------------------
    # Proxy: intercept plotting method calls
    # ------------------------------------------------------------------

    def __getattr__(self, name):
        if name in DATA_METHODS:
            return self._recorder("data", name)
        if name in STATIC_METHODS:
            return self._recorder("static", name)
        if name in POST_DATA_METHODS:
            return self._recorder("post_data", name)
        raise AttributeError(f"{type(self).__name__!r} object has no attribute {name!r}")

    def _recorder(self, kind, method):
        """Return a callable that appends a call record to ``self._calls``."""

        def record(*args, **kwargs):
            # Pop dim before storing so it never bleeds into the subplot call.
            dim = kwargs.pop("dim", None)
            self._calls.append({"kind": kind, "method": method, "args": args, "kwargs": kwargs, "dim": dim})
            return self

        return record

    # ------------------------------------------------------------------
    # title() is not in DATA/STATIC/POST_DATA so needs an explicit method
    # ------------------------------------------------------------------

    def title(self, label=None, **kwargs):
        """Record a per-frame title template.

        Placeholders such as ``{variable_name}`` and ``{time:%Y%m%d}`` are
        resolved from each frame's data layers after they are plotted.

        Parameters
        ----------
        label : str, optional
            The title format string.
        **kwargs
            Additional keyword arguments forwarded to ``Subplot.title()``.
        """
        self._title_template = label
        self._title_kwargs = kwargs
        return self

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @property
    def _subplot(self):
        """Convenience accessor for the primary (first) subplot."""
        return self._subplots[0]

    def _n_frames(self):
        """Return the total frame count from the first recorded data call."""
        data_calls = [c for c in self._calls if c["kind"] == "data"]
        if not data_calls:
            raise RuntimeError(
                f"No data plotting calls recorded. Call e.g. chart.contourf(data) before using {type(self).__name__}."
            )
        first = data_calls[0]
        return n_slices(first["args"][0], dim=first["dim"])

    def _render_statics(self, subplot):
        """Apply coastlines, gridlines, and other static features to *subplot*."""
        for call in self._calls:
            if call["kind"] == "static":
                getattr(subplot, call["method"])(*call["args"], **call["kwargs"])

    def _render_post_data(self, subplot):
        """Apply legend and similar post-data decorators to *subplot*."""
        for call in self._calls:
            if call["kind"] == "post_data":
                getattr(subplot, call["method"])(*call["args"], **call["kwargs"])

    def _render_data(self, subplot, frame_index):
        """Replace the subplot's data layers with those for *frame_index*."""
        remove_data_layers(subplot)
        for call in self._calls:
            if call["kind"] != "data":
                continue
            slice_ = iter_data(call["args"][0], frame_index, dim=call["dim"])
            getattr(subplot, call["method"])(slice_, *call["args"][1:], **call["kwargs"])

    def _apply_title(self, subplot):
        """Resolve and apply the recorded title template to *subplot*."""
        if self._title_template is not None:
            subplot.title(self._title_template, **self._title_kwargs)

    def _render_first_frame(self, subplot):
        """Render frame 0: statics first, then data, then post-data, then title.

        Statics are rendered before data so that coastlines etc. are in place
        when the domain is auto-fitted from the first frame's data extent.
        """
        self._render_statics(subplot)
        self._render_data(subplot, 0)
        self._render_post_data(subplot)
        self._apply_title(subplot)

    def _render_frame(self, subplot, frame_index):
        """Update *subplot* for frames 1+: replace data layers and title."""
        self._render_data(subplot, frame_index)
        self._apply_title(subplot)

    def _live_figure(self):
        """Return ``(figure, subplot)`` reusing the user's existing Figure.

        Used by the interactive display path (Browser.show).  No new Figure is
        constructed — the subplot the user passed in is used directly, so frame
        0 is rendered onto the axes that are already configured with the correct
        projection, domain, and figsize.
        """
        sp = self._subplot
        return sp.figure, sp

    def _build_figure(self):
        """Construct a fresh ``(Figure, Map)`` pair from the primary subplot's geometry.

        Used by the sequential/threaded Batch paths and multiprocess workers,
        which need a clean Figure isolated from the user's session.
        """
        from earthkit.plots.components.figures import Figure

        sp = self._subplot
        domain = getattr(sp, "_domain", None) or getattr(sp, "domain", None)
        crs = getattr(sp, "_crs", None)
        figsize = sp.fig.get_size_inches().tolist() if sp.fig is not None else None

        figure = Figure(rows=1, columns=1, figsize=figsize, chainable=True)
        subplot = figure.add_map(domain=domain, crs=crs)
        return figure, subplot
