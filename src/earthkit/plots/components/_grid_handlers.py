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
Grid-type dispatch and coordinate-wrapping helpers for the plotting pipeline.

This module sits between the pipeline orchestration (_pipeline.py) and the
low-level grid renderers (resample/healpix.py, resample/octahedral.py).  It
is responsible for:

- Routing pcolormesh calls for structured/unstructured grids to the correct
  backend (``_handle_specialized_grids``).
- Providing a fast NN pixel-sampling path for regular grids when the source
  and target CRS differ (``_handle_regular_grid_nn``).
- Wrapping coordinates at the antimeridian for global contour plots
  (``_handle_cyclic_points``).
- Adjusting transform-first settings for projections that do not support it
  (``_handle_transform_settings``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
from cartopy.util import add_cyclic_point

from earthkit.plots.geography import coordinate_reference_systems
from earthkit.plots.resample.grids import needs_cyclic_point

if TYPE_CHECKING:
    from earthkit.plots.styles import Style


def _handle_specialized_grids(
    subplot: Any,
    source: Any,
    z_values: np.ndarray,
    style: Style,
    method_name: str,
    kwargs: dict[str, Any],
    resample: Any = None,
    use_nn_sampling: bool = False,
) -> Any | None:
    """
    Route ``pcolormesh`` calls for non-regular grids to the correct backend.

    Returns a matplotlib mappable when it handles the render itself, or
    ``None`` to signal that the caller should proceed with the normal path.

    For ``contourf`` and all other method names this is always a no-op (returns
    ``None``) because those methods do not require special grid handling here.

    Parameters
    ----------
    subplot:
        The target subplot.
    source:
        Data source; provides ``gridspec`` and coordinate arrays.
    z_values:
        Data values to plot.
    style:
        The active style object.
    method_name:
        Name of the plotting method; only ``"pcolormesh"`` is handled here.
    kwargs:
        Live kwargs dict from the caller.
    resample:
        The active resample strategy; used to detect whether a ``Regrid``
        step is present (suppresses the structured-grid error).
    use_nn_sampling:
        When ``True`` (set by ``grid_cells``), activate the nearest-neighbour
        pixel-sampling path.  When ``False``, only validation is performed for
        structured grids.

    Returns
    -------
    mappable or None
    """
    if method_name != "pcolormesh":
        return None

    gridspec = source.gridspec

    # Validate that structured grids are not passed to pcolormesh without a
    # Regrid step.  grid_cells() suppresses this check via use_nn_sampling.
    if gridspec is not None and not use_nn_sampling:
        from earthkit.plots.resample import Chain, _is_structured_grid
        from earthkit.plots.resample import Regrid as _Regrid

        if _is_structured_grid(gridspec):
            _has_regrid = isinstance(resample, _Regrid) or (
                isinstance(resample, Chain) and any(isinstance(s, _Regrid) for s in resample.data_steps)
            )
            if not _has_regrid:
                _grid_label = {
                    "healpix": "HEALPix",
                    "reduced_gg": "reduced Gaussian",
                    "orca": "ORCA",
                }.get(gridspec.name, gridspec.name)
                raise ValueError(
                    f"Input data was identified as a {_grid_label} grid "
                    f"({gridspec.name!r}), which must be regridded onto a regular "
                    "lat/lon grid before it can be visualised with pcolormesh. "
                    "Pass resample=Regrid() (or a Chain that includes Regrid as its "
                    "first data step) to perform the regridding explicitly, or pass "
                    "resample='auto' to let earthkit-plots choose the best approach "
                    "automatically. For all available options see the "
                    "earthkit.plots.resample module documentation. "
                    "Alternatively, use grid_cells() for automatic cell rendering."
                )

    if not use_nn_sampling:
        return None

    # Specialised grid backends (HEALPix, octahedral reduced Gaussian, ORCA).
    if gridspec is not None:
        grid_handlers = {
            "healpix": _plot_healpix,
            "reduced_gg": _plot_octahedral,
            "orca": _plot_orca,
        }
        handler = grid_handlers.get(gridspec.name)
        if handler is not None:
            return handler(subplot, source, z_values, style, kwargs)

    # Fast NN pixel-sampling for regular (non-structured) grids with a CRS mismatch.
    return _handle_regular_grid_nn(subplot, source, z_values, style, kwargs)


def _handle_regular_grid_nn(
    subplot: Any,
    source: Any,
    z_values: np.ndarray,
    style: Style,
    kwargs: dict[str, Any],
) -> Any | None:
    """
    Fast nearest-neighbour pixel-sampling for regular rectilinear grids.

    Activated when the source CRS differs from the target (map) CRS.  For each
    output pixel the centre is back-transformed to the source CRS and the
    nearest source cell is found by ``numpy.searchsorted`` on the 1-D source
    axes — no interpolation, O(nx×ny), crisp cell boundaries.

    Returns a mappable if the fast path was taken, ``None`` if the caller
    should fall through to plain pcolormesh rendering.
    """
    import cartopy.crs as ccrs

    if not hasattr(subplot, "crs") or subplot.crs is None:
        return None

    target_crs = subplot.crs
    data_crs = source.crs or kwargs.get("transform") or ccrs.PlateCarree()

    # Only activate on a genuine CRS mismatch.
    if type(data_crs).__name__ == type(target_crs).__name__:
        return None

    # Only applies to regular rectilinear (meshgrid) sources.
    x_values = source.x.values
    y_values = source.y.values
    if x_values.ndim != 2 or y_values.ndim != 2:
        return None
    if not (np.allclose(x_values, x_values[0, :]) and np.allclose(y_values.T, y_values[:, 0])):
        return None

    x_src_1d = x_values[0, :]
    y_src_1d = y_values[:, 0]

    try:
        bbox_target = subplot.ax.get_extent(crs=target_crs)
    except AttributeError:
        if subplot.domain is not None:
            bbox_target = subplot.domain.bbox.to_cartopy_bounds()
        else:
            bbox_target = (-180, 180, -90, 90)

    from earthkit.plots.resample.reproject import _reproject_nn

    image, extent = _reproject_nn(
        x_src_1d,
        y_src_1d,
        z_values,
        crs_src=data_crs,
        bbox_target=bbox_target,
        crs_target=target_crs,
    )

    plot_kwargs = dict(kwargs)
    if style is not None:
        plot_kwargs.update(style.to_pcolormesh_kwargs(image))
    plot_kwargs.pop("transform", None)
    plot_kwargs.pop("transform_first", None)
    plot_kwargs.setdefault("interpolation", "nearest")

    return subplot.ax.imshow(image, extent=extent, origin="lower", **plot_kwargs)


def _plot_healpix(
    subplot: Any,
    source: Any,
    z_values: np.ndarray,
    style: Style,
    kwargs: dict[str, Any],
) -> Any:
    """Render HEALPix grid data via the nearest-neighbour imshow backend."""
    from earthkit.plots.resample import healpix

    nest = source.metadata("orderingConvention", default=None) == "nested"
    kwargs["transform"] = subplot.crs
    return healpix.nnshow(z_values, ax=subplot.ax, nest=nest, style=style, **kwargs)


def _plot_octahedral(
    subplot: Any,
    source: Any,
    z_values: np.ndarray,
    style: Style,
    kwargs: dict[str, Any],
) -> Any:
    """Render octahedral reduced Gaussian grid data via the nnshow backend."""
    from earthkit.plots.resample import octahedral

    return octahedral.nnshow(
        source.x.values,
        source.y.values,
        z_values,
        subplot.ax,
        style=style,
        **kwargs,
    )


def _plot_orca(
    subplot: Any,
    source: Any,
    z_values: np.ndarray,
    style: Style,
    kwargs: dict[str, Any],
) -> Any:
    """Render ORCA curvilinear grid data via KD-tree nearest-neighbour imshow."""
    from earthkit.plots.resample import orca

    return orca.nnshow(
        source.x.values,
        source.y.values,
        z_values,
        subplot.ax,
        style=style,
        **kwargs,
    )


def _handle_cyclic_points(
    x_values: np.ndarray,
    y_values: np.ndarray,
    z_values: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Add a cyclic longitude column to ensure global contour plots wrap correctly.

    When the data spans the full longitude range but is missing the closing
    column at 360°/−180°, contourf leaves a gap at the antimeridian.
    ``cartopy.util.add_cyclic_point`` inserts the missing column.

    This is a no-op when the data does not need a cyclic point.
    """
    if not needs_cyclic_point(x_values):
        return x_values, y_values, z_values

    # add_cyclic_point expects 1-D longitude; extract from a 2-D meshgrid if needed.
    n_x = None
    if x_values.ndim != 1:
        n_x = x_values.shape[0]
        x_values = x_values[0]

    z_values, x_values = add_cyclic_point(z_values, coord=x_values)

    # Restore 2-D meshgrid structure.
    if n_x is not None:
        x_values = np.tile(x_values, (n_x, 1))
        y_values = np.hstack((y_values, y_values[:, -1][:, np.newaxis]))

    return x_values, y_values, z_values


def _handle_transform_settings(
    subplot: Any,
    kwargs: dict[str, Any],
) -> dict[str, Any]:
    """
    Disable ``transform_first`` for projections that do not support it.

    Some cartopy projections cannot apply ``transform_first=True``; passing it
    raises an error at render time.  This guard silently flips the flag to
    ``False`` for those projections.
    """
    if "transform_first" in kwargs:
        if subplot.crs.__class__ in coordinate_reference_systems.CANNOT_TRANSFORM_FIRST:
            kwargs["transform_first"] = False
    return kwargs
