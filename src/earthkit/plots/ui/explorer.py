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

"""Explorer: interactive Jupyter control panel for earthkit-plots Maps.

Usage::

    explorer = Explorer(domain="Europe")
    explorer.contourf(data, style="auto")
    explorer.coastlines()
    explorer.title("ERA5 {variable_name}")
    explorer.legend()
    explorer.show()

The control panel renders a map alongside Domain Type / Domain / Projection
dropdowns.  Changing any control rebuilds the Figure from the recorded calls
and updates the output in-place — no cell re-execution needed.
"""

import io

from earthkit.plots.frames._base import ChartBase
from earthkit.plots.ui import controls

# CSS for the control bar and loader spinner, injected once on show().
_PANEL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto&display=swap');
.ekp-explorer .widget-label,
.ekp-explorer .widget-readout,
.ekp-explorer .widget-dropdown select {
    font-family: 'Roboto', sans-serif !important;
}
.ekp-explorer-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
    padding: 6px 0;
    border-bottom: 1px solid #ddd;
    margin-bottom: 6px;
}
</style>
"""

_LOADER_HTML = """
<div style="display:flex;align-items:center;gap:10px;padding:12px;
            font-family:'Roboto',sans-serif;color:#555;">
  <div style="width:24px;height:24px;border:3px solid #ddd;
              border-top-color:#555;border-radius:50%;
              animation:ekp-spin 0.8s linear infinite;"></div>
  <span>Rendering…</span>
</div>
<style>
  @keyframes ekp-spin {{ from{{transform:rotate(0deg)}} to{{transform:rotate(360deg)}} }}
</style>
"""


class Explorer(ChartBase):
    """Interactive map control panel for Jupyter notebooks.

    Records plotting calls (same mechanism as ``Slider`` and ``Batch``) and
    replays them whenever the user changes the domain or projection.  The
    figure is always rebuilt from scratch so cartopy's projection-baked axes
    are never reused.

    Parameters
    ----------
    domain : str or list, optional
        Initial domain — passed directly to ``Map(domain=...)``.  The domain
        dropdowns are pre-selected to match.
    crs : cartopy.crs.CRS, optional
        Initial projection.  The projection dropdown is pre-selected to match
        if a matching label exists; otherwise it defaults to "Auto".
    figsize : tuple of float, optional
        Figure size ``(width, height)`` in inches.
    **figure_kwargs
        Additional keyword arguments forwarded to ``Figure()``.
    """

    def __init__(self, domain=None, crs=None, figsize=None, **figure_kwargs):
        super().__init__(domain=domain, crs=crs, figsize=figsize, **figure_kwargs)

    def show(self):
        """Render the map and display it alongside the control panel.

        Raises
        ------
        ImportError
            If ``ipywidgets`` is not installed.
        """
        try:
            import ipywidgets as widgets
            from IPython.display import HTML, display
        except ImportError:
            raise ImportError("ipywidgets is required for Explorer. Install it with: pip install ipywidgets")

        import matplotlib.pyplot as plt

        display(HTML(_PANEL_CSS))

        # --- Initial CRS label ---
        initial_crs_label = self._crs_label(self._crs)

        # --- Resolve initial domain type and name ---
        initial_type, initial_name = self._resolve_initial_domain(self._domain)

        # --- Build controls ---
        type_w, domain_w, get_domain = controls.domain_selector(
            initial_type=initial_type,
            initial_domain=initial_name,
            widgets=widgets,
        )
        proj_w, get_crs = controls.projection_selector(
            initial=initial_crs_label,
            widgets=widgets,
        )

        map_out = widgets.Output()
        loader_out = widgets.Output()

        def render():
            """Rebuild the figure with current control values and update output."""
            domain = get_domain()
            crs = get_crs()

            with loader_out:
                loader_out.clear_output(wait=True)
                display(HTML(_LOADER_HTML))

            figure, subplot = self._build_figure_with(domain=domain, crs=crs)
            self._render_first_frame(subplot)

            buf = io.BytesIO()
            figure.fig.savefig(buf, format="png", bbox_inches="tight")
            plt.close(figure.fig)

            with loader_out:
                loader_out.clear_output(wait=True)

            with map_out:
                from IPython.display import Image

                map_out.clear_output(wait=True)
                display(Image(data=buf.getvalue()))

        def on_change(_change):
            render()

        domain_w.observe(on_change, names="value")
        proj_w.observe(on_change, names="value")

        # --- Layout ---
        control_bar = widgets.HBox(
            [type_w, domain_w, proj_w],
            layout=widgets.Layout(
                flex_wrap="wrap",
                align_items="center",
                gap="8px",
                width="100%",
            ),
        )
        control_bar.add_class("ekp-explorer-bar")

        panel = widgets.VBox(
            [control_bar, loader_out, map_out],
            layout=widgets.Layout(width="100%"),
        )
        panel.add_class("ekp-explorer")

        display(panel)
        render()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_figure_with(self, domain, crs):
        """Build a fresh Figure and Map with the given *domain* and *crs*.

        Overrides the domain/crs from the constructor so controls take effect.

        Parameters
        ----------
        domain : str or None
        crs : cartopy.crs.CRS or None

        Returns
        -------
        tuple of (Figure, Map)
        """
        from earthkit.plots.components.figures import Figure

        figure = Figure(
            rows=1,
            columns=1,
            figsize=self._figsize,
            chainable=True,
            **self._figure_kwargs,
        )
        subplot = figure.add_map(domain=domain, crs=crs)
        return figure, subplot

    @staticmethod
    def _crs_label(crs):
        """Return the dropdown label that best matches *crs*.

        Parameters
        ----------
        crs : cartopy.crs.CRS or None

        Returns
        -------
        str
            A label from ``controls.PROJECTION_LABELS``, defaulting to
            ``"Auto"`` when no match is found.
        """
        if crs is None:
            return "Auto"
        for label, cls, _ in controls.PROJECTIONS:
            if cls is not None and isinstance(crs, cls):
                return label
        return "Auto"

    @staticmethod
    def _resolve_initial_domain(domain):
        """Return ``(domain_type, domain_name)`` for the domain dropdowns.

        Parameters
        ----------
        domain : str, list, or None

        Returns
        -------
        tuple of (str, str)
        """
        if domain is None:
            return "Global", "Global"

        if isinstance(domain, (list, tuple)):
            # Custom bounding box — not representable as a named domain; fall
            # back to Global so the dropdowns start in a valid state.
            return "Global", "Global"

        # Check whether the name is a preset continental/regional domain.
        preset = controls.preset_domains()
        if domain in preset:
            if domain == "Global":
                return "Global", "Global"
            return "Continent/Region", domain

        # Assume it is a country name.
        return "Country", domain
