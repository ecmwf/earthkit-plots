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

"""Batch: produce one output file per field in a dataset.

Usage::

    fig = Figure(figsize=(10, 6))
    m = fig.add_map(domain="Europe")

    batch = Batch(m, workers="threaded")
    batch.contourf(data, style="auto")
    batch.coastlines()
    batch.legend()
    batch.title("ERA5 {variable_name} - {time:%B %Y}")

    paths = batch.save("{variable_name}_{time:%Y%m%d}.png")

Nothing is rendered until ``save()`` is called.
"""

import os

from earthkit.plots.frames._artists import remove_data_layers
from earthkit.plots.frames._base import (
    ChartBase,
    has_placeholders,
    iter_data,
    slugify_path,
)


class Batch(ChartBase):
    """Produce one output file per field, reusing the supplied Figure between frames.

    Parameters
    ----------
    subplot : Subplot, Map, or list thereof
        The subplot(s) to drive.  Must already be attached to a Figure.
    workers : False, ``"threaded"``, or ``"multiprocess"``, optional
        Concurrency strategy for rendering frames (default ``False``).

        - ``False`` — sequential, single-threaded.
        - ``"threaded"`` — ``ThreadPoolExecutor``; data-loading and file I/O
          can overlap, matplotlib drawing is still serialised by a lock.
        - ``"multiprocess"`` — ``ProcessPoolExecutor``; each worker process
          builds its own Figure from the recorded calls.
    """

    _VALID_WORKERS = (False, "threaded", "multiprocess")

    def __init__(self, subplot, workers=False):
        if workers not in self._VALID_WORKERS:
            raise ValueError(f"workers={workers!r} is not supported. Choose one of: {list(self._VALID_WORKERS)}.")
        super().__init__(subplot)
        self._workers = workers

    def save(self, path_template, dpi=150, **savefig_kwargs):
        """Render all frames and write one file per frame.

        Parameters
        ----------
        path_template : str
            Output filename template.  May contain metadata placeholders such
            as ``"{variable_name}_{time:%Y%m%d}.png"``.  When no placeholders
            are present, a zero-padded frame index is appended automatically.
        dpi : int, optional
            Output resolution in dots per inch (default 150).
        **savefig_kwargs
            Additional keyword arguments forwarded to
            ``matplotlib.figure.Figure.savefig()``.

        Returns
        -------
        list of str
            Absolute paths of every file written, in frame order.
        """
        n_frames = self._n_frames()

        if self._workers == "multiprocess":
            return self._save_multiprocess(path_template, n_frames, dpi, savefig_kwargs)
        if self._workers == "threaded":
            return self._save_threaded(path_template, n_frames, dpi)
        return self._save_sequential(path_template, n_frames, dpi)

    def _save_sequential(self, path_template, n_frames, dpi):
        figure, subplot = self._build_figure()
        with_placeholders = has_placeholders(path_template)

        self._render_first_frame(subplot)
        paths = [self._write_frame(figure, subplot, 0, path_template, with_placeholders, dpi)]

        for i in range(1, n_frames):
            self._render_frame(subplot, i)
            paths.append(self._write_frame(figure, subplot, i, path_template, with_placeholders, dpi))

        return paths

    def _save_threaded(self, path_template, n_frames, dpi):
        import threading
        from concurrent.futures import ThreadPoolExecutor

        figure, subplot = self._build_figure()
        with_placeholders = has_placeholders(path_template)

        self._render_first_frame(subplot)
        paths = [self._write_frame(figure, subplot, 0, path_template, with_placeholders, dpi)]

        lock = threading.Lock()
        remaining = [None] * (n_frames - 1)

        def render(i):
            with lock:
                self._render_frame(subplot, i)
                remaining[i - 1] = self._write_frame(figure, subplot, i, path_template, with_placeholders, dpi)

        max_workers = min(n_frames - 1, os.cpu_count() or 4)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            list(executor.map(render, range(1, n_frames)))

        return paths + remaining

    def _save_multiprocess(self, path_template, n_frames, dpi, savefig_kwargs):
        from concurrent.futures import ProcessPoolExecutor

        sp = self._subplot
        domain = getattr(sp, "_domain", None) or getattr(sp, "domain", None)
        crs = getattr(sp, "_crs", None)
        figsize = sp.fig.get_size_inches().tolist() if sp.fig is not None else None

        worker_args = (
            self._calls,
            domain,
            crs,
            figsize,
            self._title_template,
            self._title_kwargs,
            path_template,
            dpi,
            savefig_kwargs,
            has_placeholders(path_template),
        )

        max_workers = min(n_frames, os.cpu_count() or 4)
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_render_frame_worker, i, *worker_args) for i in range(n_frames)]
            return [f.result() for f in futures]

    def _resolve_path(self, subplot, frame_index, path_template, with_placeholders):
        if with_placeholders and subplot.layers:
            out_path = subplot.format_string(path_template)
        elif not with_placeholders:
            base, ext = os.path.splitext(path_template)
            out_path = f"{base}_{frame_index:04d}{ext}"
        else:
            out_path = path_template
        return os.path.abspath(slugify_path(out_path))

    def _write_frame(self, figure, subplot, frame_index, path_template, with_placeholders, dpi):
        out_path = self._resolve_path(subplot, frame_index, path_template, with_placeholders)
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        figure.fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
        return out_path


def _render_frame_worker(
    frame_index,
    calls,
    domain,
    crs,
    figsize,
    title_template,
    title_kwargs,
    path_template,
    dpi,
    savefig_kwargs,
    with_placeholders,
):
    """Render one frame in a worker process with its own fresh Figure."""
    import os

    from earthkit.plots.frames._base import slugify_path
    from earthkit.plots.components.figures import Figure

    figure = Figure(rows=1, columns=1, figsize=figsize, chainable=True)
    subplot = figure.add_map(domain=domain, crs=crs)

    for call in calls:
        if call["kind"] == "static":
            getattr(subplot, call["method"])(*call["args"], **call["kwargs"])

    remove_data_layers(subplot)
    for call in calls:
        if call["kind"] != "data":
            continue
        slice_ = iter_data(call["args"][0], frame_index, dim=call["dim"])
        getattr(subplot, call["method"])(slice_, *call["args"][1:], **call["kwargs"])

    for call in calls:
        if call["kind"] == "post_data":
            getattr(subplot, call["method"])(*call["args"], **call["kwargs"])

    if title_template is not None:
        subplot.title(title_template, **title_kwargs)

    if with_placeholders and subplot.layers:
        out_path = subplot.format_string(path_template)
    elif not with_placeholders:
        base, ext = os.path.splitext(path_template)
        out_path = f"{base}_{frame_index:04d}{ext}"
    else:
        out_path = path_template

    out_path = os.path.abspath(slugify_path(out_path))
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    figure.fig.savefig(out_path, dpi=dpi, bbox_inches="tight", **savefig_kwargs)
    return out_path
