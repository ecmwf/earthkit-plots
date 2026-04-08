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

"""Slider: animate over a dataset in a Jupyter notebook.

Usage::

    slider = Slider(domain="Europe")
    slider.contourf(data, units="celsius", style="auto")
    slider.title("ERA5 {variable_name} - {time:%B %Y}")
    slider.legend()
    slider.coastlines()
    slider.gridlines()

    slider.show()                                    # integer slider
    slider.show(picker="select")                     # formatted datetime labels
    slider.show(picker="datetime", frequency="daily")

Nothing is rendered until ``show()`` is called.
"""

import calendar
import datetime
import io
import multiprocessing
import threading
import weakref

from earthkit.plots.animation._artists import remove_data_layers
from earthkit.plots.animation._base import ChartBase, extract_datetimes, iter_data

# How many frames ahead must be cached before the player unblocks the loader.
PLAYER_LOOKAHEAD = 4

# Default playback interval in milliseconds.
PLAYER_DEFAULT_INTERVAL = 500

# CSS spinner injected while frames are being prefetched.
_LOADER_HTML = """
<div style="display:flex;align-items:center;gap:10px;font-family:'Roboto',sans-serif;">
  <div style="width:28px;height:28px;border:4px solid #ddd;
              border-top-color:#555;border-radius:50%;
              animation:ekp-spin 0.8s linear infinite;"></div>
  <span style="color:#555;">Generating frames…</span>
</div>
<style>
  @keyframes ekp-spin {{ from{{transform:rotate(0deg)}} to{{transform:rotate(360deg)}} }}
</style>
"""

# Default strftime formats for each temporal frequency.
FREQUENCY_FORMATS = {
    "hourly":  "%d %b %Y %H:%M",
    "daily":   "%d %b %Y",
    "monthly": "%b %Y",
    "yearly":  "%Y",
}


def _render_frame_to_bytes(frame_index, calls, domain, crs, figsize, figure_kwargs,
                           title_template, title_kwargs, quality_resolution, result_queue):
    """Render one frame in a worker process and put PNG bytes onto *result_queue*.

    Designed to be the target of a ``multiprocessing.Process``.  Each worker
    builds its own fresh Figure so there is no shared matplotlib state.

    Parameters
    ----------
    frame_index : int
    calls : list
        Recorded call list from ``Slider._calls``.
    domain, crs, figsize, figure_kwargs, title_template, title_kwargs
        Forwarded to Figure/subplot construction.
    quality_resolution : tuple of (int, int) or None
        ``(nx, ny)`` passed to ``Bilinear`` when quality resampling is active.
    result_queue : multiprocessing.Queue
        Receives ``(frame_index, png_bytes)`` on success or
        ``(frame_index, None)`` on failure.
    """
    try:
        import io as _io

        from earthkit.plots.animation._artists import remove_data_layers
        from earthkit.plots.animation._base import iter_data
        from earthkit.plots.components.figures import Figure

        figure = Figure(rows=1, columns=1, figsize=figsize, chainable=True, **figure_kwargs)
        subplot = figure.add_map(domain=domain, crs=crs)

        for call in calls:
            if call["kind"] == "static":
                getattr(subplot, call["method"])(*call["args"], **call["kwargs"])

        remove_data_layers(subplot)
        for call in calls:
            if call["kind"] != "data":
                continue
            kwargs = call["kwargs"]
            if quality_resolution is not None and "resample" not in kwargs:
                from earthkit.plots.resample import Bilinear
                nx, ny = quality_resolution
                kwargs = {**kwargs, "resample": Bilinear(nx, ny)}
            slice_ = iter_data(call["args"][0], frame_index)
            getattr(subplot, call["method"])(slice_, *call["args"][1:], **kwargs)

        for call in calls:
            if call["kind"] == "post_data":
                getattr(subplot, call["method"])(*call["args"], **call["kwargs"])

        if title_template is not None:
            subplot.title(title_template, **title_kwargs)

        buf = _io.BytesIO()
        figure.fig.savefig(buf, format="png", bbox_inches="tight")
        result_queue.put((frame_index, buf.getvalue()))
    except Exception:
        result_queue.put((frame_index, None))


class _Prefetcher:
    """Prefetch animation frames into a shared cache using worker processes.

    Frames are rendered one at a time in order, each in its own
    ``multiprocessing.Process``.  Results are drained from a
    ``multiprocessing.Queue`` by a background thread and written into
    *frame_cache*.  Callers can stop prefetching at any time by calling
    ``stop()``.

    Parameters
    ----------
    start_index : int
        First frame to render.
    n_frames : int
        Total number of frames.
    calls : list
        Recorded call list from ``Slider._calls``.
    domain, crs, figsize, figure_kwargs, title_template, title_kwargs
        Forwarded to each worker process.
    quality_resolution : tuple of (int, int) or None
    frame_cache : dict
        Shared dict into which ``{frame_index: png_bytes}`` entries are
        written as workers complete.
    on_frame_cached : callable or None
        Called with ``frame_index`` each time a new frame lands in the cache.
    """

    def __init__(self, start_index, n_frames, calls, domain, crs, figsize,
                 figure_kwargs, title_template, title_kwargs, quality_resolution,
                 frame_cache, on_frame_cached=None):
        self._stop_event = threading.Event()
        self._worker_args = (calls, domain, crs, figsize, figure_kwargs,
                             title_template, title_kwargs, quality_resolution)
        self._start_index = start_index
        self._n_frames = n_frames
        self._frame_cache = frame_cache
        self._on_frame_cached = on_frame_cached

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """Signal the prefetch loop to stop after the current frame completes."""
        self._stop_event.set()

    def _run(self):
        calls, domain, crs, figsize, figure_kwargs, title_template, title_kwargs, quality_resolution = self._worker_args
        ctx = multiprocessing.get_context("spawn")

        for i in range(self._start_index, self._n_frames):
            if self._stop_event.is_set():
                break
            if i in self._frame_cache:
                continue

            queue = ctx.Queue()
            proc = ctx.Process(
                target=_render_frame_to_bytes,
                args=(i, calls, domain, crs, figsize, figure_kwargs,
                      title_template, title_kwargs, quality_resolution, queue),
                daemon=True,
            )
            proc.start()

            # Poll for the result, checking the stop event so we don't block
            # indefinitely when stop() is called while a worker is running.
            result = None
            while result is None:
                if self._stop_event.is_set():
                    proc.terminate()
                    proc.join(timeout=2)
                    return
                try:
                    result = queue.get(timeout=0.2)
                except Exception:
                    pass

            proc.join()
            frame_index, png_bytes = result
            if png_bytes is not None:
                self._frame_cache[frame_index] = png_bytes
                if self._on_frame_cached is not None:
                    self._on_frame_cached(frame_index)


def _draw_mappable(fig, mappable):
    """Draw *mappable* onto *fig* for the blit display path.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
    mappable : matplotlib artist
        A ContourSet (handled via ``.collections``) or any other Artist.
    """
    import matplotlib.artist as martist

    if isinstance(mappable, martist.Artist):
        fig.draw_artist(mappable)
    elif hasattr(mappable, "collections"):
        for artist in mappable.collections:
            fig.draw_artist(artist)


class Slider(ChartBase):
    """Animate over a dataset with a Jupyter widgets slider.

    Only the field at the current slider position is loaded — no other slices
    are fetched.  The full plotting pipeline runs once for the first frame to
    configure styles, grids, and static layers; subsequent frames replace only
    the data artists.

    Parameters
    ----------
    domain : str or list, optional
        Named domain (e.g. ``"Europe"``) or bounding box
        ``[lon_min, lon_max, lat_min, lat_max]``.
    crs : cartopy.crs.CRS, optional
        Map projection.  Auto-selected from the domain when omitted.
    figsize : tuple of float, optional
        Figure size ``(width, height)`` in inches.
    quality : str, optional
        Resampling quality for data layers.  One of ``"low"``, ``"medium"``,
        ``"high"``, or ``"very high"``.
    **figure_kwargs
        Additional keyword arguments forwarded to ``Figure()``.
    """

    QUALITY_RESOLUTIONS = {
        "very high": (1000, 1000),
        "high":      (500, 500),
        "medium":    (250, 250),
        "low":       (100, 100),
    }

    def __init__(self, domain=None, crs=None, figsize=None, quality=None, **figure_kwargs):
        if quality is not None and quality not in self.QUALITY_RESOLUTIONS:
            raise ValueError(
                f"quality={quality!r} is not supported. "
                f"Choose one of: {list(self.QUALITY_RESOLUTIONS)} or None."
            )
        super().__init__(domain=domain, crs=crs, figsize=figsize, **figure_kwargs)
        self._figure = None
        self._subplot = None
        self._quality = quality
        # PNG bytes keyed by frame index, populated lazily on first visit.
        # Stored in memory only — cleared automatically when the Slider is
        # garbage-collected, and released at interpreter exit via atexit.
        self._frame_cache = {}
        # Clear the cache when the Slider is GC'd or the interpreter exits.
        weakref.finalize(self, self._frame_cache.clear)

    def show(self, picker="slider", frequency=None, picker_format=None, interval=None):
        """Render the first frame and display an interactive picker widget.

        Parameters
        ----------
        picker : str, optional
            Widget type for navigating frames:

            - ``"slider"`` (default) — integer slider ``0 … n-1``.
            - ``"select"`` — ``SelectionSlider`` with formatted datetime labels.
            - ``"date"`` — ``DatePicker`` calendar widget.
            - ``"datetime"`` — time picker controlled by *frequency*.
            - ``"player"`` — ``Play`` widget that prefetches frames in the
              background using worker processes and plays them back smoothly.

            The ``"select"``, ``"date"``, and ``"datetime"`` modes require time
            metadata in the data; a ``ValueError`` is raised if unavailable.
        frequency : str, optional
            Granularity for ``picker="datetime"``: ``"hourly"``, ``"daily"``,
            ``"monthly"``, or ``"yearly"``.  Defaults to ``"hourly"``.
            Ignored for other picker types.
        picker_format : str, optional
            ``strftime`` format for datetime labels in the ``"select"`` and
            ``"slider"`` pickers.  Defaults to the format for *frequency*.
        interval : int, optional
            Playback interval in milliseconds for ``picker="player"``
            (default ``500``).  Ignored for other picker types.

        Raises
        ------
        ImportError
            If ``ipywidgets`` is not installed.
        ValueError
            If a datetime-based picker is requested but the data has no time
            metadata, or an unsupported picker/frequency value is given.
        """
        try:
            import ipywidgets as widgets
            from IPython.display import HTML, display
        except ImportError:
            raise ImportError(
                "ipywidgets is required for Slider. "
                "Install it with: pip install ipywidgets"
            )

        display(HTML(
            "<style>"
            "@import url('https://fonts.googleapis.com/css2?family=Roboto&display=swap');"
            ".widget-label, .widget-readout, .widget-button, "
            ".widget-dropdown select, .widget-datepicker input { "
            "font-family: 'Roboto', sans-serif !important; }"
            "</style>"
        ))

        import matplotlib

        n_frames = self._n_frames()
        self._figure, self._subplot = self._build_figure()
        self._render_first_frame(self._subplot)

        if picker == "player":
            self._show_player(n_frames, interval or PLAYER_DEFAULT_INTERVAL, widgets, display)
            import matplotlib.pyplot as plt
            plt.close(self._figure.fig)
            return

        inner, to_index, step = self._build_picker(
            picker, n_frames, frequency, picker_format, widgets
        )
        widget = self._add_step_buttons(inner, step, widgets)

        backend = matplotlib.get_backend().lower()
        uses_widget_canvas = "widget" in backend or "ipympl" in backend or "nbagg" in backend

        if uses_widget_canvas:
            self._show_blit(widget, to_index, display)
        else:
            self._show_output(widget, to_index, widgets, display)
            import matplotlib.pyplot as plt
            plt.close(self._figure.fig)

    # ------------------------------------------------------------------
    # Picker construction
    # ------------------------------------------------------------------

    def _frame_datetimes(self, n_frames):
        """Return per-frame datetimes from the first data call, or None.

        Parameters
        ----------
        n_frames : int

        Returns
        -------
        list of datetime.datetime or None
        """
        data_calls = [c for c in self._calls if c["kind"] == "data"]
        if not data_calls:
            return None
        return extract_datetimes(data_calls[0]["args"][0], n_frames)

    def _frame_datetime_bounds(self, n_frames):
        """Return ``(first_dt, last_dt)`` without iterating every frame.

        Parameters
        ----------
        n_frames : int

        Returns
        -------
        tuple of (datetime.datetime or None, datetime.datetime or None)
        """
        from earthkit.plots.sources import get_source

        data_calls = [c for c in self._calls if c["kind"] == "data"]
        if not data_calls:
            return None, None

        data = data_calls[0]["args"][0]

        def get_dt(index):
            src = get_source(iter_data(data, index))
            dt_info = src.datetime()
            return dt_info.get("valid_time") if dt_info else None

        return get_dt(0), get_dt(n_frames - 1)

    def _build_picker(self, picker, n_frames, frequency, picker_format, widgets):
        """Return ``(widget, to_index, step)`` for the requested picker type.

        ``to_index(value)`` maps the widget's current value to a frame index.
        ``step(delta)`` advances the picker by *delta* positions (±1).

        Parameters
        ----------
        picker : str
        n_frames : int
        frequency : str or None
        picker_format : str or None
        widgets : module
            The ``ipywidgets`` module.

        Returns
        -------
        tuple of (widget, callable, callable)
        """
        if picker == "slider":
            return self._integer_slider(n_frames, frequency, picker_format, widgets)

        if picker == "datetime":
            return self._datetime_picker(n_frames, frequency or "hourly", widgets)

        if picker == "player":
            # Player has its own display path — signal show() to use it.
            return None, None, None

        # Remaining modes require per-frame datetimes.
        datetimes = self._frame_datetimes(n_frames)
        if datetimes is None:
            raise ValueError(
                f"picker={picker!r} requires time metadata in the data, "
                "but none was found.  Use picker='slider' or ensure your "
                "data has valid_time / time coordinates."
            )
        dt_to_index = {dt: i for i, dt in enumerate(datetimes)}

        if picker == "select":
            return self._selection_slider(datetimes, dt_to_index, picker_format, widgets)

        if picker == "date":
            return self._date_picker(datetimes, widgets)

        raise ValueError(
            f"picker={picker!r} is not supported. "
            "Choose 'slider', 'select', 'date', or 'datetime'."
        )

    def _integer_slider(self, n_frames, frequency, picker_format, widgets):
        """Return an integer ``IntSlider`` widget, optionally with a datetime label.

        Parameters
        ----------
        n_frames : int
        frequency : str or None
        picker_format : str or None
        widgets : module

        Returns
        -------
        tuple of (widget, callable, callable)
        """
        fmt = picker_format or FREQUENCY_FORMATS.get(frequency, FREQUENCY_FORMATS["hourly"])
        first_dt, last_dt = self._frame_datetime_bounds(n_frames)

        slider = widgets.IntSlider(
            value=0, min=0, max=n_frames - 1, step=1,
            description="Frame:",
            continuous_update=False,
            layout=widgets.Layout(flex="1 1 auto", min_width="200px"),
        )

        def step(delta):
            slider.value = max(0, min(n_frames - 1, slider.value + delta))

        if first_dt is None:
            return slider, int, step

        # Annotate with a datetime label derived from a uniform time step.
        step_size = (last_dt - first_dt) / max(n_frames - 1, 1)

        def index_to_dt(i):
            return first_dt + step_size * i

        label = widgets.Label(
            value=index_to_dt(0).strftime(fmt),
            layout=widgets.Layout(min_width="160px"),
        )
        slider.observe(lambda change: label.__setattr__("value", index_to_dt(change["new"]).strftime(fmt)), names="value")

        container = widgets.HBox(
            [slider, label],
            layout=widgets.Layout(align_items="center", width="100%"),
        )
        # Delegate .observe to the slider so the display paths wire up correctly.
        container.observe = slider.observe

        return container, int, step

    def _selection_slider(self, datetimes, dt_to_index, picker_format, widgets):
        """Return a ``SelectionSlider`` with formatted datetime options.

        Parameters
        ----------
        datetimes : list of datetime.datetime
        dt_to_index : dict
        picker_format : str or None
        widgets : module

        Returns
        -------
        tuple of (widget, callable, callable)
        """
        fmt = picker_format or "%d %b %Y %H:%M"
        options = [(dt.strftime(fmt), dt) for dt in datetimes]
        values = [dt for _, dt in options]

        w = widgets.SelectionSlider(
            options=options,
            value=datetimes[0],
            description="Time:",
            continuous_update=False,
            layout=widgets.Layout(width="80%"),
        )

        def step(delta):
            idx = values.index(w.value)
            w.value = values[max(0, min(len(values) - 1, idx + delta))]

        return w, lambda v: dt_to_index[v], step

    def _date_picker(self, datetimes, widgets):
        """Return a ``DatePicker`` widget.

        Parameters
        ----------
        datetimes : list of datetime.datetime
        widgets : module

        Returns
        -------
        tuple of (widget, callable, callable)
        """
        date_to_index = {dt.date(): i for i, dt in enumerate(datetimes)}
        dates = sorted(date_to_index)

        w = widgets.DatePicker(value=datetimes[0].date(), description="Date:")

        def step(delta):
            idx = dates.index(w.value)
            w.value = dates[max(0, min(len(dates) - 1, idx + delta))]

        return w, lambda v: date_to_index[v], step

    def _datetime_picker(self, n_frames, frequency, widgets):
        """Return a datetime-based picker widget for the given *frequency*.

        Parameters
        ----------
        n_frames : int
        frequency : str
            One of ``"hourly"``, ``"daily"``, ``"monthly"``, ``"yearly"``.
        widgets : module

        Returns
        -------
        tuple of (widget, callable, callable)

        Raises
        ------
        ValueError
            If time metadata is unavailable, or *frequency* is unsupported.
        """
        first_dt, last_dt = self._frame_datetime_bounds(n_frames)
        if first_dt is None:
            raise ValueError(
                "picker='datetime' requires time metadata in the data, "
                "but none was found.  Use picker='slider' or ensure your "
                "data has valid_time / time coordinates."
            )

        if frequency == "hourly":
            return self._hourly_picker(n_frames, first_dt, last_dt, widgets)
        if frequency == "daily":
            return self._daily_picker(n_frames, first_dt, last_dt, widgets)
        if frequency == "monthly":
            return self._monthly_picker(n_frames, first_dt, last_dt, widgets)
        if frequency == "yearly":
            return self._yearly_picker(n_frames, first_dt, last_dt, widgets)

        raise ValueError(
            f"frequency={frequency!r} is not supported for picker='datetime'. "
            "Choose 'hourly', 'daily', 'monthly', or 'yearly'."
        )

    def _hourly_picker(self, n_frames, first_dt, last_dt, widgets):
        step_size = (last_dt - first_dt) / (n_frames - 1)

        w = widgets.NaiveDatetimePicker(
            value=first_dt, min=first_dt, max=last_dt, description="Time:"
        )

        def to_index(v):
            idx = round((v - first_dt) / step_size)
            return max(0, min(n_frames - 1, idx))

        def step(delta):
            w.value = max(first_dt, min(last_dt, w.value + step_size * delta))

        return w, to_index, step

    def _daily_picker(self, n_frames, first_dt, last_dt, widgets):
        first_date = first_dt.date()
        last_date = last_dt.date()
        total_days = (last_date - first_date).days

        w = widgets.DatePicker(value=first_date, min=first_date, max=last_date, description="Date:")

        def to_index(v):
            if total_days == 0:
                return 0
            frac = (v - first_date).days / total_days
            return max(0, min(n_frames - 1, round(frac * (n_frames - 1))))

        def step(delta):
            w.value = max(first_date, min(last_date, w.value + datetime.timedelta(days=delta)))

        return w, to_index, step

    def _monthly_picker(self, n_frames, first_dt, last_dt, widgets):
        """Return a linked year + month dropdown pair for monthly navigation.

        The month dropdown options are constrained to months that exist in the
        data for the selected year, so partial years are handled correctly.

        Parameters
        ----------
        n_frames : int
        first_dt, last_dt : datetime.datetime
        widgets : module

        Returns
        -------
        tuple of (widget, callable, callable)
        """
        year_month_to_index = self._build_year_month_index(n_frames, first_dt, last_dt)

        # Flat sorted list of (year, month) pairs for step navigation.
        all_ym = sorted(
            (y, m)
            for y, months in year_month_to_index.items()
            for m in months
        )

        years = sorted(year_month_to_index)
        first_months = sorted(year_month_to_index[years[0]])

        def month_options(year):
            return [
                (calendar.month_abbr[m], m)
                for m in sorted(year_month_to_index[year])
            ]

        year_w = widgets.Dropdown(
            options=[(str(y), y) for y in years],
            value=years[0],
            description="Year:",
            layout=widgets.Layout(width="auto"),
            style={"description_width": "initial"},
        )
        month_w = widgets.Dropdown(
            options=month_options(years[0]),
            value=first_months[0],
            description="Month:",
            layout=widgets.Layout(width="auto"),
            style={"description_width": "initial"},
        )

        def on_year_change(change):
            new_options = month_options(change["new"])
            month_w.options = new_options
            valid = [m for _, m in new_options]
            if month_w.value not in valid:
                month_w.value = valid[0]

        year_w.observe(on_year_change, names="value")

        container = widgets.HBox([year_w, month_w])

        def to_index(_ignored):
            return year_month_to_index[year_w.value][month_w.value]

        def step(delta):
            current = (year_w.value, month_w.value)
            new_y, new_m = all_ym[max(0, min(len(all_ym) - 1, all_ym.index(current) + delta))]
            # Set year first so month options update before the month value is set.
            year_w.value = new_y
            month_w.value = new_m

        # HBox has no "value" trait; wire both dropdowns to forward any outer
        # observer so the blit/output display paths work without modification.
        outer_observer = [None]

        def forward(_change):
            if outer_observer[0] is not None:
                outer_observer[0]({"new": (year_w.value, month_w.value)})

        def observe(fn, names="value"):  # noqa: ARG001
            outer_observer[0] = fn
            year_w.observe(forward, names="value")
            month_w.observe(forward, names="value")

        container.observe = observe
        return container, to_index, step

    def _yearly_picker(self, n_frames, first_dt, last_dt, widgets):
        year_to_index = self._build_year_index(n_frames, first_dt, last_dt)
        years = sorted(year_to_index)

        w = widgets.Dropdown(
            options=[(str(y), y) for y in years], value=years[0], description="Year:"
        )

        def step(delta):
            idx = years.index(w.value)
            w.value = years[max(0, min(len(years) - 1, idx + delta))]

        return w, lambda v: year_to_index.get(v, 0), step

    # ------------------------------------------------------------------
    # Temporal index builders
    # ------------------------------------------------------------------

    def _build_year_month_index(self, n_frames, first_dt, last_dt):
        """Return ``{year: {month: frame_index}}`` for the first frame of each month.

        Uses a stride-based scan to avoid a full O(n) pass over all frames.

        Parameters
        ----------
        n_frames : int
        first_dt, last_dt : datetime.datetime

        Returns
        -------
        dict
        """
        from earthkit.plots.sources import get_source

        data_calls = [c for c in self._calls if c["kind"] == "data"]
        data = data_calls[0]["args"][0]

        def get_dt(index):
            src = get_source(iter_data(data, index))
            dt_info = src.datetime()
            return dt_info.get("valid_time") if dt_info else None

        total_months = (
            (last_dt.year - first_dt.year) * 12
            + (last_dt.month - first_dt.month)
            + 1
        )
        stride = max(1, n_frames // (total_months + 1))

        result = {}
        seen = set()

        for i in range(0, n_frames, stride):
            dt = get_dt(i)
            if dt is None:
                continue
            key = (dt.year, dt.month)
            if key not in seen:
                # Walk backwards to find the true first frame of this month.
                j = i
                while j > 0 and get_dt(j - 1) is not None:
                    prev = get_dt(j - 1)
                    if (prev.year, prev.month) != key:
                        break
                    j -= 1
                seen.add(key)
                result.setdefault(dt.year, {})[dt.month] = j

        # Ensure the last frame's month is always included.
        last_key = (last_dt.year, last_dt.month)
        if last_key not in seen:
            j = n_frames - 1
            while j > 0:
                prev = get_dt(j - 1)
                if prev is None or (prev.year, prev.month) != last_key:
                    break
                j -= 1
            result.setdefault(last_dt.year, {})[last_dt.month] = j

        return result

    def _build_year_index(self, n_frames, first_dt, last_dt):
        """Return ``{year: frame_index}`` for the first frame of each year.

        Parameters
        ----------
        n_frames : int
        first_dt, last_dt : datetime.datetime

        Returns
        -------
        dict
        """
        ym = self._build_year_month_index(n_frames, first_dt, last_dt)
        return {year: min(months.values()) for year, months in ym.items()}

    # ------------------------------------------------------------------
    # Widget layout helpers
    # ------------------------------------------------------------------

    def _add_step_buttons(self, inner, step, widgets):
        """Wrap *inner* with previous/next step buttons.

        Parameters
        ----------
        inner : ipywidgets widget
        step : callable
            ``step(delta)`` advances the picker by *delta* positions.
        widgets : module

        Returns
        -------
        ipywidgets.HBox
            The container delegates ``.observe()`` to *inner*.
        """
        btn_layout = widgets.Layout(width="36px", height="36px", padding="0px")
        prev_btn = widgets.Button(description="◀", layout=btn_layout)
        next_btn = widgets.Button(description="▶", layout=btn_layout)

        prev_btn.on_click(lambda _: step(-1))
        next_btn.on_click(lambda _: step(+1))

        container = widgets.HBox(
            [prev_btn, inner, next_btn],
            layout=widgets.Layout(align_items="center", width="100%"),
        )
        container.observe = inner.observe
        return container

    # ------------------------------------------------------------------
    # Data rendering (overrides base to support quality resampling)
    # ------------------------------------------------------------------

    def _render_data(self, subplot, frame_index):
        """Replace data layers, injecting a ``resample`` kwarg when quality is set.

        Parameters
        ----------
        subplot : Subplot
        frame_index : int
        """
        from earthkit.plots.resample import Bilinear

        remove_data_layers(subplot)
        for call in self._calls:
            if call["kind"] != "data":
                continue
            data = call["args"][0]
            rest = call["args"][1:]
            slice_ = iter_data(data, frame_index)
            kwargs = call["kwargs"]
            if self._quality is not None and "resample" not in kwargs:
                nx, ny = self.QUALITY_RESOLUTIONS[self._quality]
                kwargs = {**kwargs, "resample": Bilinear(nx, ny)}
            getattr(subplot, call["method"])(slice_, *rest, **kwargs)

    def _update_frame(self, frame_index):
        """Replace data layers for *frame_index* on the live subplot.

        Parameters
        ----------
        frame_index : int
        """
        self._render_data(self._subplot, frame_index)
        self._apply_title(self._subplot)

    # ------------------------------------------------------------------
    # Display paths
    # ------------------------------------------------------------------

    def _show_player(self, n_frames, interval, widgets, display):
        """Display a Play widget that prefetches frames via worker processes.

        Pressing play starts a ``_Prefetcher`` from the first uncached frame at
        or after the current position.  The Output widget shows a loader until
        ``PLAYER_LOOKAHEAD`` frames are ready ahead of the current position,
        then plays back from the cache.  Pausing or stopping kills the prefetch
        process.

        Parameters
        ----------
        n_frames : int
        interval : int
            Playback interval in milliseconds.
        widgets : module
        display : callable
        """
        from IPython.display import HTML, Image

        # Cache frame 0, already rendered by _render_first_frame.
        buf = io.BytesIO()
        self._figure.fig.savefig(buf, format="png", bbox_inches="tight")
        self._frame_cache[0] = buf.getvalue()

        quality_resolution = (
            self.QUALITY_RESOLUTIONS[self._quality] if self._quality else None
        )

        # max starts at 0 and grows as frames are cached, preventing the Play
        # widget from advancing past the prefetch frontier.
        play = widgets.Play(
            value=0, min=0, max=0, step=1,
            interval=interval,
            description="Play",
            disabled=True,
        )
        slider = widgets.IntSlider(
            value=0, min=0, max=0,
            continuous_update=False,
            disabled=True,
            layout=widgets.Layout(flex="1 1 auto", min_width="200px"),
        )
        # Python-side link so every value change fires our observe callbacks.
        widgets.link((play, "value"), (slider, "value"))

        frame_out = widgets.Output()
        loader_out = widgets.Output()

        prefetcher = [None]  # mutable container so closures can replace it

        def _frames_ahead(index):
            """Count consecutive cached frames starting at *index*."""
            count = 0
            for j in range(index, n_frames):
                if j in self._frame_cache:
                    count += 1
                else:
                    break
            return count

        def _first_uncached_from(index):
            """Return the first uncached frame index >= *index*."""
            for j in range(index, n_frames):
                if j not in self._frame_cache:
                    return j
            return None

        def _show_loader():
            with loader_out:
                loader_out.clear_output(wait=True)
                display(HTML(_LOADER_HTML))

        def _hide_loader():
            with loader_out:
                loader_out.clear_output(wait=True)

        def _show_frame(index):
            with frame_out:
                frame_out.clear_output(wait=True)
                display(Image(data=self._frame_cache[index]))

        def _render_and_cache(index):
            """Render *index* on the main process and cache it (manual scrub)."""
            self._update_frame(index)
            buf = io.BytesIO()
            self._figure.fig.savefig(buf, format="png", bbox_inches="tight")
            self._frame_cache[index] = buf.getvalue()

        def _stop_prefetcher():
            if prefetcher[0] is not None:
                prefetcher[0].stop()
                prefetcher[0] = None

        def _start_prefetcher(from_index):
            _stop_prefetcher()
            start = _first_uncached_from(from_index)
            if start is None:
                return  # everything already cached
            prefetcher[0] = _Prefetcher(
                start_index=start,
                n_frames=n_frames,
                calls=self._calls,
                domain=self._domain,
                crs=self._crs,
                figsize=self._figsize,
                figure_kwargs=self._figure_kwargs,
                title_template=self._title_template,
                title_kwargs=self._title_kwargs,
                quality_resolution=quality_resolution,
                frame_cache=self._frame_cache,
                on_frame_cached=lambda _: _on_frame_cached(),
            )

        def _highest_consecutive_cached():
            """Return the highest frame index reachable without a cache gap from 0."""
            high = -1
            for j in range(n_frames):
                if j in self._frame_cache:
                    high = j
                else:
                    break
            return high

        def _on_frame_cached():
            # Called from the prefetch thread each time a new frame lands.
            # Advance play.max to the edge of the contiguous cached region so
            # the Play widget cannot move past what is ready.
            high = _highest_consecutive_cached()
            if high > play.max:
                play.max = high
                slider.max = high

            current = slider.value
            if _frames_ahead(current) < PLAYER_LOOKAHEAD:
                return
            # Unlock the full range once everything is cached.
            if len(self._frame_cache) == n_frames:
                play.max = n_frames - 1
                slider.max = n_frames - 1

            # Enough lookahead — enable controls if still locked, hide loader.
            if play.disabled:
                play.disabled = False
                slider.disabled = False
                _hide_loader()
            elif not play.playing:
                # Catch-up after the player paused waiting for frames.
                _hide_loader()
                play.play()

        def _on_play_change(change):
            playing = change["new"]
            if playing:
                _start_prefetcher(slider.value)
            else:
                _stop_prefetcher()

        def _on_slider_change(change):
            index = change["new"]
            if index in self._frame_cache:
                _show_frame(index)
                # If playing and lookahead is too low, pause and wait.
                if play.playing and _frames_ahead(index) < PLAYER_LOOKAHEAD:
                    play.pause()
                    _show_loader()
            else:
                if play.playing:
                    # Prefetch will handle it; show loader and pause until ready.
                    play.pause()
                    _show_loader()
                else:
                    # Manual scrub to an uncached frame — render it immediately.
                    _render_and_cache(index)
                    _show_frame(index)

        play.observe(_on_play_change, names="_playing")
        slider.observe(_on_slider_change, names="value")

        # Start the initial prefetch and show the loader until ready.
        _show_loader()
        _show_frame(0)
        _start_prefetcher(0)

        controls = widgets.HBox(
            [play, slider],
            layout=widgets.Layout(align_items="center", width="100%"),
        )
        display(widgets.VBox([loader_out, frame_out, controls]))

    def _show_blit(self, widget, to_index, display):
        """Display the figure using matplotlib blit (ipympl backend).

        Previously rendered frames are served from ``self._frame_cache``
        (PNG bytes) rather than re-running the plotting pipeline.

        Parameters
        ----------
        widget : ipywidgets widget
        to_index : callable
        display : callable
            ``IPython.display.display``
        """
        import io

        from IPython.display import Image

        canvas = self._figure.fig.canvas
        fig = self._figure.fig

        canvas.draw()
        bg = canvas.copy_from_bbox(fig.bbox)

        # Cache frame 0, which has already been rendered by _render_first_frame.
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
        self._frame_cache[0] = buf.getvalue()

        def on_change(change):
            frame_index = to_index(change["new"])

            if frame_index in self._frame_cache:
                # Restore the static background, then overlay the cached PNG.
                canvas.restore_region(bg)
                display(Image(data=self._frame_cache[frame_index]))
                canvas.blit(fig.bbox)
                canvas.flush_events()
                return

            canvas.restore_region(bg)
            self._update_frame(frame_index)
            for layer in self._subplot.layers:
                _draw_mappable(fig, layer.mappable)
            fig.draw_artist(self._subplot.ax.title)
            canvas.blit(fig.bbox)
            canvas.flush_events()

            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight")
            self._frame_cache[frame_index] = buf.getvalue()

        widget.observe(on_change, names="value")
        display(fig.canvas)
        display(widget)

    def _show_output(self, widget, to_index, widgets, display):
        """Display the figure by re-rendering to PNG in an Output widget.

        Used as a fallback for non-blit backends (e.g. the inline backend).
        Previously rendered frames are served from ``self._frame_cache``
        (PNG bytes) rather than re-running the plotting pipeline.

        Parameters
        ----------
        widget : ipywidgets widget
        to_index : callable
        widgets : module
        display : callable
        """
        import io

        from IPython.display import Image

        out = widgets.Output()

        def fig_to_png():
            buf = io.BytesIO()
            self._figure.fig.savefig(buf, format="png", bbox_inches="tight")
            buf.seek(0)
            return buf.read()

        # Cache frame 0, which has already been rendered by _render_first_frame.
        self._frame_cache[0] = fig_to_png()

        def on_change(change):
            frame_index = to_index(change["new"])
            if frame_index not in self._frame_cache:
                self._update_frame(frame_index)
                self._frame_cache[frame_index] = fig_to_png()
            with out:
                out.clear_output(wait=True)
                display(Image(data=self._frame_cache[frame_index]))

        widget.observe(on_change, names="value")

        with out:
            display(Image(data=self._frame_cache[0]))

        display(widgets.VBox([out, widget]))
