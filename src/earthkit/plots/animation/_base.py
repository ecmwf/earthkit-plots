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

from earthkit.plots.animation._artists import remove_data_layers


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


def iter_data(data, index):
    """Return the *index*-th slice of *data* without loading other slices.

    Parameters
    ----------
    data : earthkit.data.FieldList, xarray.DataArray, xarray.Dataset, or sequence
        The dataset to slice.
    index : int
        The frame index to extract.

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
            dim = list(data.dims)[0]
            return data.isel({dim: index})
    except ImportError:
        pass

    return data[index]


def n_slices(data):
    """Return the total number of slices in *data*.

    Parameters
    ----------
    data : earthkit.data.FieldList, xarray.DataArray, xarray.Dataset, or sequence
        The dataset to measure.

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
            dim = list(data.dims)[0]
            return data.sizes[dim]
    except ImportError:
        pass

    return len(data)


def extract_datetimes(data, n):
    """Return a list of datetimes, one per frame, or None if unavailable.

    Parameters
    ----------
    data : dataset
        The dataset from which to extract time metadata.
    n : int
        Number of frames.

    Returns
    -------
    list of datetime.datetime or None
    """
    from earthkit.plots.sources import get_source

    datetimes = []
    for i in range(n):
        src = get_source(iter_data(data, i))
        dt_info = src.datetime()
        vt = dt_info.get("valid_time") if dt_info else None
        if vt is None:
            return None
        datetimes.append(vt)
    return datetimes


def has_placeholders(template):
    """Return True if *template* contains any ``{...}`` format placeholders.

    Parameters
    ----------
    template : str
        The format string to check.

    Returns
    -------
    bool
    """
    return any(
        field is not None
        for _, field, _, _ in string.Formatter().parse(template)
    )


def slugify_path(path):
    """Replace spaces with underscores in the filename component of *path*.

    Parameters
    ----------
    path : str
        A file path whose filename may contain spaces.

    Returns
    -------
    str
    """
    head, tail = os.path.split(path)
    tail = tail.replace(" ", "_")
    return os.path.join(head, tail) if head else tail


class ChartBase:
    """Call-recording base for Batch and Slider.

    Records plotting calls made against the chart object and replays them
    frame-by-frame during rendering.  Subclasses implement
    ``_on_frame_rendered(subplot, frame_index)`` to decide what to do with
    each rendered frame (save to file, update a widget, etc.).

    Parameters
    ----------
    domain : str or list, optional
        Named domain or bounding box ``[lon_min, lon_max, lat_min, lat_max]``.
    crs : cartopy.crs.CRS, optional
        Map projection.
    figsize : tuple of float, optional
        Figure size ``(width, height)`` in inches.
    **figure_kwargs
        Additional keyword arguments forwarded to ``Figure()``.
    """

    def __init__(self, domain=None, crs=None, figsize=None, **figure_kwargs):
        self._domain = domain
        self._crs = crs
        self._figsize = figsize
        self._figure_kwargs = figure_kwargs

        # Each entry: {"kind": "data"|"static"|"post_data", "method": str,
        #              "args": tuple, "kwargs": dict}
        self._calls = []

        self._title_template = None
        self._title_kwargs = {}

    def __getattr__(self, name):
        if name in DATA_METHODS:
            return self._recorder("data", name)
        if name in STATIC_METHODS:
            return self._recorder("static", name)
        if name in POST_DATA_METHODS:
            return self._recorder("post_data", name)
        raise AttributeError(
            f"{type(self).__name__!r} object has no attribute {name!r}"
        )

    def _recorder(self, kind, method):
        """Return a callable that appends a call record to ``self._calls``."""
        def record(*args, **kwargs):
            self._calls.append(
                {"kind": kind, "method": method, "args": args, "kwargs": kwargs}
            )
            return self
        return record

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

    def _build_figure(self):
        """Construct and return a fresh ``(Figure, Map)`` pair."""
        from earthkit.plots.components.figures import Figure

        figure = Figure(
            rows=1,
            columns=1,
            figsize=self._figsize,
            chainable=True,
            **self._figure_kwargs,
        )
        subplot = figure.add_map(domain=self._domain, crs=self._crs)
        return figure, subplot

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
        """Replace the subplot's data layers with those for *frame_index*.

        Parameters
        ----------
        subplot : Subplot
        frame_index : int
        """
        remove_data_layers(subplot)
        for call in self._calls:
            if call["kind"] != "data":
                continue
            data = call["args"][0]
            rest = call["args"][1:]
            slice_ = iter_data(data, frame_index)
            getattr(subplot, call["method"])(slice_, *rest, **call["kwargs"])

    def _apply_title(self, subplot):
        """Resolve and apply the recorded title template to *subplot*."""
        if self._title_template is not None:
            subplot.title(self._title_template, **self._title_kwargs)

    def _render_first_frame(self, subplot):
        """Render frame 0: data first, then static features, legend, and title.

        Data is rendered before statics so the pipeline can auto-detect
        the domain and normalise longitudes before axes extent and cartopy
        features are configured.
        """
        self._render_data(subplot, 0)
        self._render_statics(subplot)
        self._render_post_data(subplot)
        self._apply_title(subplot)

    def _render_frame(self, subplot, frame_index):
        """Update *subplot* for frames 1+: replace data layers and title.

        Parameters
        ----------
        subplot : Subplot
        frame_index : int
        """
        self._render_data(subplot, frame_index)
        self._apply_title(subplot)

    def _n_frames(self):
        """Return the total frame count from the first recorded data call.

        Returns
        -------
        int

        Raises
        ------
        RuntimeError
            If no data plotting calls have been recorded.
        """
        data_calls = [c for c in self._calls if c["kind"] == "data"]
        if not data_calls:
            raise RuntimeError(
                f"No data plotting calls recorded. "
                f"Call e.g. chart.contourf(data) before using "
                f"{type(self).__name__}."
            )
        return n_slices(data_calls[0]["args"][0])
