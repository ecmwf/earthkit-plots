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
Core plotting pipeline: data extraction → style → render → Layer.

Each ``extract_plottables_*`` function is the single entry point for one class
of plot call.  They share a numbered step convention:

  Step 0   _prepare_style_and_units  — resolve named styles, back-fill units
  Step 1   _infer_plot_context        — geographic vs cartesian, 1D vs 2D
  Step 2   get_source                 — wrap data in a unified Source object
  Step 3   configure_style            — build/resolve the Style object
  Step 4   apply_scale_factor         — style-level scaling (e.g. Pa → hPa)
  Step 5   apply_sampling             — stride-based data thinning
  Step 6   _apply_data_resampling     — Regrid / Unstructured / generic Resample
  Step 7   domain extraction          — clip to subplot domain if requested
  Step 8   _apply_pixel_sampling      — Bilinear / NearestNeighbour reprojection
  Step 9   _handle_cyclic_points      — antimeridian wrapping for contour plots
  Step 10  _handle_transform_settings — disable transform_first where unsupported
  Step 11  matplotlib call            — via style.method_name(ax, x, y, z, ...)
  Step 12  Layer creation             — wrap mappable + source in a Layer

Vector plots (extract_plottables_vector_2D) follow the same pattern but handle
two component arrays (u, v) and reproject each independently.
"""

from __future__ import annotations

import warnings
from typing import Any

import numpy as np

from earthkit.plots.components._grid_handlers import (
    _handle_cyclic_points,
    _handle_specialized_grids,
    _handle_transform_settings,
)
from earthkit.plots.components._pixel_sampling import (
    _apply_data_resampling,
    _apply_pixel_sampling,
)
from earthkit.plots.components._style_utils import (
    _prepare_style_and_units,
    apply_sampling,
    apply_scale_factor,
    configure_style,
)
from earthkit.plots.identifiers import identify_primary_axis
from earthkit.plots.metadata.units import are_equal as _units_are_equal
from earthkit.plots.sources import get_source
from earthkit.plots.sources.context import PlotContext
from earthkit.plots.styles import Style


def _infer_plot_context(subplot: Any, method_name: str) -> PlotContext:
    """
    Infer the :class:`~earthkit.plots.sources.context.PlotContext` from the
    subplot type and method name.

    The context drives coordinate extraction inside the Source — it tells the
    extractor which dimensions are spatial vs data, and whether the plot is
    geographic.

    Parameters
    ----------
    subplot:
        The subplot instance.
    method_name:
        Name of the plotting method being called.

    Returns
    -------
    PlotContext
    """
    # Local import avoids a circular dependency at module load time
    # (maps.py → subplots.py → _pipeline.py would otherwise import maps.py).
    from earthkit.plots.components.maps import Map

    is_map = isinstance(subplot, Map)
    is_1d = method_name in ("line", "scatter", "bar", "barh", "plot", "stripes")
    is_vector = method_name in ("quiver", "barbs", "streamplot")

    if is_map:
        if is_vector:
            return PlotContext.GEOGRAPHIC_VECTOR_2D
        return PlotContext.GEOGRAPHIC_1D if is_1d else PlotContext.GEOGRAPHIC_2D
    else:
        if is_vector:
            return PlotContext.CARTESIAN_VECTOR_2D
        return PlotContext.CARTESIAN_1D if is_1d else PlotContext.CARTESIAN_2D


# ---------------------------------------------------------------------------
# 1-D pipeline (line, scatter, bar, stripes, …)
# ---------------------------------------------------------------------------


def extract_plottables_1D(
    subplot: Any,
    method_name: str,
    args: tuple[Any, ...],
    x: str | np.ndarray | list[float] | None = None,
    y: str | np.ndarray | list[float] | None = None,
    z: str | np.ndarray | list[float] | None = None,
    style: Style | str | None = None,
    no_style: bool = False,
    units: str | None = None,
    x_units: str | None = None,
    y_units: str | None = None,
    z_units: str | None = None,
    every: int | None = None,
    resample: Any = False,
    auto_style: bool = False,
    metadata: dict[str, Any] | None = None,
    label: str | None = None,
    **kwargs: Any,
) -> Any:
    """
    Extract and process data for 1-D plotting methods.

    Handles the complete pipeline for line plots, scatter plots, bar charts,
    climate stripes, and any other method that maps one dimension of data onto
    a single axis.

    Parameters
    ----------
    subplot:
        Target subplot instance.
    method_name:
        Name of the plotting method to dispatch to on the Style object.
    args:
        Positional data arguments (the first element is the data object).
    x, y, z:
        Coordinate/data specifications.  Strings are interpreted as coordinate
        names; arrays are used directly.
    style:
        Style object, ``"auto"``, a named-style string, or ``None``.
    no_style:
        When ``True``, skip style processing and call matplotlib directly.
    units:
        Target units for the primary data dimension.
    x_units, y_units, z_units:
        Dimension-specific unit overrides.
    every:
        Stride for data thinning.
    resample:
        Resampling strategy.  Pixel-samplers (Bilinear, NearestNeighbour) are
        rejected here — use ``Regrid()`` for scatter resampling.
    auto_style:
        Deprecated; use ``style="auto"`` instead.
    metadata:
        Extra metadata merged into the Source.
    label:
        Legend label (supports format-string placeholders).

    Returns
    -------
    matplotlib artist or list of artists
    """
    # Step 0: Normalise style/units and emit deprecation warning if needed.
    units, style = _prepare_style_and_units(style, units, auto_style)

    # Step 1: Infer context and build the unified Source.
    context = _infer_plot_context(subplot, method_name)
    source = get_source(
        *args,
        x=x,
        y=y,
        z=z,
        context=context,
        units=units,
        x_units=x_units,
        y_units=y_units,
        z_units=z_units,
        metadata=metadata,
    )
    kwargs.update(subplot._plot_kwargs(source))

    # Step 2: Resolve the Style object.
    style = configure_style(method_name, style, source, units, auto_style, kwargs)

    # Step 2.5: If the style carries preferred units (use_preferred_units path),
    # update the source so that unit conversion is applied when .z is accessed.
    if style._units is not None and not _units_are_equal(style._units, source.source_units):
        source.update_units(style._units)

    # Step 2.6: Determine the display units for axis routing.
    # Priority: explicit caller units → style's preferred units → source's
    # native units.  This is the value that will actually appear on the y-axis,
    # so it is the correct key for the _AxisRegistry unit→axis map.
    display_units = units or (style._units if style is not None else None) or source.source_units

    # Step 3: Apply style scale factor to z values (e.g. Pa → hPa).
    if z is not None or (source.z is not None and source.z.values is not None):
        z_values = apply_scale_factor(style, source, z)
        # apply_scale_factor returns None when source.z is None (e.g. coordinate-
        # only calls where the extractor doesn't populate source.z).
        if z_values is None and isinstance(z, np.ndarray):
            z_values = z
    else:
        z_values = None

    # Step 4: Extract x/y values (unit conversion already applied by Source).
    x_values, y_values = source.x.values, source.y.values

    # Step 4.1: Roll 0–360 longitudes to –180 to +180 if requested.
    if getattr(subplot, "_wrap_longitudes", None) == "x" and np.any(x_values > 180):
        from earthkit.plots.geography.domains import force_minus_180_to_180

        sort_idx = np.argsort(force_minus_180_to_180(x_values))
        x_values = force_minus_180_to_180(x_values)[sort_idx]
        y_values = y_values[sort_idx]
    elif getattr(subplot, "_wrap_longitudes", None) == "y" and np.any(y_values > 180):
        from earthkit.plots.geography.domains import force_minus_180_to_180

        sort_idx = np.argsort(force_minus_180_to_180(y_values))
        y_values = force_minus_180_to_180(y_values)[sort_idx]
        x_values = x_values[sort_idx]

    # Step 5: Stride-based thinning.
    x_values, y_values, z_values = apply_sampling(x_values, y_values, z_values, every)

    # Step 5.1: Clip to subplot domain.
    if subplot.domain is not None:
        x_values, y_values, z_values = subplot.domain.extract(x_values, y_values, z_values, source_crs=source.crs)

    # Step 5.5: Data-space resampling.
    # Pixel-samplers are rejected here (allow_pixel_samplers=False) because
    # they produce a regular image grid that is meaningless for scatter-like
    # plots.  The error message directs the user to Regrid() instead.
    x_values, y_values, z_values, _ = _apply_data_resampling(
        x_values,
        y_values,
        z_values,
        resample,
        source,
        subplot,
        method_name,
        allow_pixel_samplers=False,
        kwargs=kwargs,
    )

    # Step 6: no_style path injects the 'c' kwarg as z values.
    if no_style and z_values is None:
        z_values = kwargs.pop("c", None)

    # Step 7: Resolve the target axes and render.
    # _resolve_render_ax handles all three routing cases:
    #   1. explicit twin_axis() context  →  current_ax
    #   2. auto_twin_axes disabled / no units  →  primary ax
    #   3. unit-based auto-routing via _AxisRegistry  →  find-or-create twinx()
    render_ax = subplot._resolve_render_ax(display_units)
    mappable = getattr(style, method_name)(render_ax, x_values, y_values, z_values, **kwargs)

    # Step 8: Create the Layer and attach it to the subplot.
    from earthkit.plots.components.layers import Layer

    primary_axis = identify_primary_axis(source, source._x_spec, source._y_spec)

    axis_units: dict[str, str] = {}
    if x_units is not None:
        axis_units["x"] = x_units
    if y_units is not None:
        axis_units["y"] = y_units
    if units is not None and primary_axis is not None and primary_axis not in axis_units:
        axis_units[primary_axis] = units

    layer = Layer(
        source,
        mappable,
        subplot,
        style,
        primary_axis=primary_axis,
        axis_units=axis_units,
    )
    # Record which axes this layer was rendered onto so that AxisView.ylabel()
    # and Subplot.ylabel() can auto-label each axis from its own layers.
    layer.render_ax = render_ax

    if label is not None:
        label = layer.format_string(label)
        if isinstance(mappable, list):
            # For grouped calls (colorby= etc.) only the first line gets a
            # legend entry; the rest are hidden.
            for i, m in enumerate(mappable):
                m.set_label(label if i == 0 else "_nolegend_")
        else:
            mappable.set_label(label)

    subplot.layers.append(layer)
    return mappable


# ---------------------------------------------------------------------------
# 2-D pipeline (contourf, contour, pcolormesh, scatter on maps, …)
# ---------------------------------------------------------------------------


def extract_plottables_2D(
    subplot: Any,
    method_name: str,
    args: tuple[Any, ...],
    x: str | np.ndarray | list[float] | None = None,
    y: str | np.ndarray | list[float] | None = None,
    z: str | np.ndarray | list[float] | None = None,
    style: Style | str | None = None,
    no_style: bool = False,
    units: str | None = None,
    x_units: str | None = None,
    y_units: str | None = None,
    z_units: str | None = None,
    every: int | None = None,
    extract_domain: bool = False,
    auto_style: bool = False,
    metadata: dict[str, Any] | None = None,
    resample: Any = None,
    grid: Any = "auto",
    use_nn_sampling: bool = False,
    **kwargs: Any,
) -> Any:
    """
    Extract and process data for 2-D plotting methods.

    Handles contourf, contour, pcolormesh, and point_cloud on both geographic
    (Map) and cartesian (Subplot) axes.  Includes the full resampling pipeline
    (data-space and pixel-space), cyclic-point wrapping, domain clipping, and
    specialized grid dispatch (HEALPix, octahedral).

    Parameters
    ----------
    subplot:
        Target subplot instance.
    method_name:
        Plotting method name (``"contourf"``, ``"pcolormesh"``, …).
    args:
        Positional data arguments.
    x, y, z:
        Coordinate/data specifications.
    style:
        Style object, ``"auto"``, a named-style string, or ``None``.
    no_style:
        When ``True``, call matplotlib directly (bypass Style).
    units:
        Target units for z values.
    x_units, y_units, z_units:
        Dimension-specific unit overrides.
    every:
        Stride for data thinning.
    extract_domain:
        When ``True``, clip data to the subplot's domain before rendering.
    auto_style:
        Deprecated; use ``style="auto"`` instead.
    metadata:
        Extra metadata merged into the Source.
    resample:
        Resampling strategy.  ``None`` defers to the method's default (usually
        ``_AUTO``); ``False`` disables resampling entirely.
    grid:
        Grid specification override; ``"auto"`` uses the source's own gridspec.
    use_nn_sampling:
        Internal flag set by ``grid_cells()`` to activate the NN pixel-sampling
        path for structured and regular rectilinear grids.

    Returns
    -------
    matplotlib artist
    """
    # Step 0: Normalise style/units.
    units, style = _prepare_style_and_units(style, units, auto_style)

    from earthkit.plots.resample import _AUTO, Unstructured

    # Translate the legacy `interpolate` kwarg to `resample`.
    if "interpolate" in kwargs and resample is None:
        interp = kwargs.pop("interpolate")
        warnings.warn(
            "The 'interpolate' keyword argument is deprecated. Use 'resample=Unstructured(...)' instead.",
            DeprecationWarning,
            stacklevel=5,
        )
        if interp is True:
            resample = Unstructured()
        elif isinstance(interp, dict):
            resample = Unstructured(**interp)
        elif isinstance(interp, Unstructured):
            resample = interp

    _resample_is_auto = resample == _AUTO

    # Step 1: Infer context.
    context = _infer_plot_context(subplot, method_name)

    # Step 2: Build the unified Source.
    source = get_source(
        *args,
        x=x,
        y=y,
        z=z,
        context=context,
        units=units,
        x_units=x_units,
        y_units=y_units,
        z_units=z_units,
        metadata=metadata,
    )
    kwargs.update(subplot._plot_kwargs(source))

    if grid != "auto":
        source._gridspec_override = grid

    # Step 2.5a: Auto-fit the map extent to the data when no domain is set.
    # This handles the case where the user passes crs= but no domain=: we derive
    # the extent from the data's coordinate bounding box reprojected into the
    # target CRS, so the axes are zoomed to the data rather than showing a global
    # view.
    if subplot.domain is None and hasattr(subplot, "crs") and source.crs is not None:
        try:
            import cartopy.crs as _ccrs

            from earthkit.plots.geography import domains as _domains
            from earthkit.plots.geography.domains import force_minus_180_to_180

            x_ext = source.x.values.squeeze()
            y_ext = source.y.values.squeeze()
            if isinstance(source.crs, _ccrs._CylindricalProjection) and np.any(x_ext > 180):
                x_ext = force_minus_180_to_180(x_ext)
            domain = _domains.Domain.from_bbox(
                bbox=[
                    float(x_ext.min()),
                    float(x_ext.max()),
                    float(y_ext.min()),
                    float(y_ext.max()),
                ],
                source_crs=source.crs,
                target_crs=subplot.crs,
            )
            bbox_vals = list(domain.bbox)
            if None not in bbox_vals and all(np.isfinite(v) for v in bbox_vals if v is not None):
                subplot.domain = domain
                if subplot._ax is not None:
                    subplot._ax.set_extent(
                        domain.bbox.to_cartopy_bounds(),
                        domain.bbox.crs,
                    )
        except Exception:
            pass

    # Step 2.5b: Resolve resample="auto" now that we know the source gridspec.
    if _resample_is_auto:
        from earthkit.plots.resample import _is_structured_grid
        from earthkit.plots.resample.grids import is_structured as _is_regular_grid

        _healpix_structured = _is_structured_grid(source.gridspec)
        _unstructured = False
        if not _healpix_structured:
            try:
                _unstructured = not _is_regular_grid(source.x.values, source.y.values)
            except Exception:
                pass

        from earthkit.plots.components._pixel_sampling import _auto_resample_policy

        resample = _auto_resample_policy(method_name, _healpix_structured, is_unstructured=_unstructured)

    # Step 3: Resolve the Style object.
    style = configure_style(method_name, style, source, units, auto_style, kwargs)

    # Step 3.5: If the style carries preferred units (use_preferred_units path),
    # update the source so that unit conversion is applied when .z is accessed.
    if style._units is not None and not _units_are_equal(style._units, source.source_units):
        source.update_units(style._units)

    # Remove earthkit-internal schema keys that are not valid matplotlib kwargs.
    kwargs.pop("regrid", None)

    # Intercept `label` before it reaches matplotlib — ContourSet objects do
    # not participate in auto-legend, so we handle it ourselves via proxy
    # artists stored on the Layer.
    proxy_label = kwargs.pop("label", None)
    proxy_color = kwargs.get("colors") or kwargs.get("color")

    # Step 4: Apply style scale factor.
    z_values = apply_scale_factor(style, source, z)

    # Step 5: Dispatch to specialized grid handlers (HEALPix, octahedral).
    # Returns a mappable when the handler renders the plot; None otherwise.
    mappable = _handle_specialized_grids(
        subplot,
        source,
        z_values,
        style,
        method_name,
        kwargs,
        resample=resample,
        use_nn_sampling=use_nn_sampling,
    )

    if mappable is None:
        # Step 6: Extract coordinate arrays and apply stride-based thinning.
        x_values, y_values = source.x.values, source.y.values
        x_values, y_values, z_values = apply_sampling(x_values, y_values, z_values, every)

        # Step 6.5: Data-space resampling (Regrid, Unstructured, generic).
        # Pixel-samplers (Bilinear, NearestNeighbour) are deferred to Step 8.5.
        x_values, y_values, z_values, _domain_suppressed = _apply_data_resampling(
            x_values,
            y_values,
            z_values,
            resample,
            source,
            subplot,
            method_name,
            allow_pixel_samplers=True,
            kwargs=kwargs,
        )
        if _domain_suppressed:
            extract_domain = False

        # Step 7: no_style path — inject 'c' kwarg as z values.
        if no_style and z_values is None:
            z_values = kwargs.pop("c", None)

        # Step 8: Clip data to the subplot domain.
        if subplot.domain and extract_domain and not no_style:
            x_values, y_values, z_values = subplot.domain.extract(x_values, y_values, z_values, source_crs=source.crs)

        # Step 8.5: Pixel-space resampling (Bilinear / NearestNeighbour).
        # Deferred from Step 6.5 because these samplers need subplot/CRS/bbox
        # context that is unavailable at Source-construction time.
        ps_result = _apply_pixel_sampling(
            subplot,
            source,
            x_values,
            y_values,
            z_values,
            resample=resample,
            method_name=method_name,
            no_style=no_style,
            style=style,
            data_crs=source.crs or kwargs.get("transform"),
            kwargs=kwargs,
        )
        x_values, y_values, z_values = ps_result.x, ps_result.y, ps_result.z
        if ps_result.mappable is not None:
            mappable = ps_result.mappable

        # Step 9: Add cyclic longitude column for global contour plots.
        # Skipped when pixel-sampling already produced a complete regular grid.
        if method_name.startswith("contour") and not ps_result.reprojected:
            x_values, y_values, z_values = _handle_cyclic_points(x_values, y_values, z_values)

        # Step 10: Disable transform_first for unsupported projections.
        kwargs = _handle_transform_settings(subplot, kwargs)

        # Step 11: Render the plot.
        # Skipped when _apply_pixel_sampling already produced a mappable
        # (i.e. the NearestNeighbour imshow path was taken).
        if mappable is None:
            if not no_style:
                mappable = getattr(style, method_name)(subplot.current_ax, x_values, y_values, z_values, **kwargs)
            else:
                mappable = getattr(subplot.current_ax, method_name)(x_values, y_values, z_values, **kwargs)

    # Step 12: Create the Layer and attach it to the subplot.
    from earthkit.plots.components.layers import Layer

    axis_units: dict[str, str] = {}
    if x_units is not None:
        axis_units["x"] = x_units
    if y_units is not None:
        axis_units["y"] = y_units
    if units is not None and "z" not in axis_units:
        axis_units["z"] = units

    proxy_color_val = proxy_color[0] if isinstance(proxy_color, (list, tuple)) else proxy_color
    layer = Layer(
        source,
        mappable,
        subplot,
        style=style if proxy_label is None else None,
        primary_axis="z",
        axis_units=axis_units,
        proxy_label=proxy_label,
        proxy_color=proxy_color_val,
        proxy_linewidth=kwargs.get("linewidths", 1.0) if proxy_label is not None else None,
    )

    subplot.layers.append(layer)
    return mappable


# ---------------------------------------------------------------------------
# Vector 2-D pipeline (quiver, barbs)
# ---------------------------------------------------------------------------


def _resolve_vector_sources(
    args: tuple,
    x: Any,
    y: Any,
    u: Any,
    v: Any,
    context: PlotContext,
    units: str | None,
    u_units: str | None,
    v_units: str | None,
    x_units: str | None,
    y_units: str | None,
    metadata: dict | None,
) -> tuple[Any, np.ndarray, np.ndarray]:
    """
    Resolve the three calling conventions for vector plots into a unified
    ``(source, u_values, v_values)`` triple.

    Supported calling conventions
    ------------------------------
    ``subplot.quiver(data)``
        Single data object with auto-detected or explicitly named u/v variables.
    ``subplot.quiver(u=u_data, v=v_data)``
        Two separate data objects passed as keyword arguments.
    ``subplot.quiver(u_data, v_data)``
        Legacy two-positional-argument form.
    """
    if not args:
        # Keyword-only: quiver(u=..., v=...)
        if u is None or v is None:
            raise ValueError(
                "Vector plots require both u and v components. "
                "Provide as: chart.quiver(data) with auto-detection, "
                "chart.quiver(data, u='u_var', v='v_var'), or "
                "chart.quiver(u=u_data, v=v_data)"
            )
        u_source = get_source(u, x=x, y=y, context=context, units=units, metadata=metadata)
        v_source = get_source(v, x=x, y=y, context=context, units=units, metadata=metadata)
        _validate_uv_grids(u_source, v_source)
        source = u_source
        u_values = u_source.z.values.squeeze() if u_source.z else None
        v_values = v_source.z.values.squeeze() if v_source.z else None

    elif len(args) == 1:
        # Single data object — auto-detect or use explicit u/v names.
        source = get_source(
            args[0],
            x=x,
            y=y,
            u=u,
            v=v,
            context=context,
            units=units,
            u_units=u_units,
            v_units=v_units,
            x_units=x_units,
            y_units=y_units,
            metadata=metadata,
        )
        if source.u is None or source.v is None:
            raise ValueError(
                "Could not extract u and v components from data. "
                "Either specify them explicitly (u='u_var', v='v_var') or "
                "ensure the data contains recognizable U/V variable names."
            )
        u_values = source.u.values
        v_values = source.v.values

    elif len(args) == 2:
        # Legacy two-argument form: quiver(u_data, v_data)
        u_source = get_source(args[0], x=x, y=y, context=context, units=units, metadata=metadata)
        v_source = get_source(args[1], x=x, y=y, context=context, units=units, metadata=metadata)
        _validate_uv_grids(u_source, v_source)
        u_arr = (u_source.z.values if u_source.z else u_source.y.values).squeeze()
        v_arr = (v_source.z.values if v_source.z else v_source.y.values).squeeze()
        # Carry u_source metadata into the rebuilt source so it has long_name etc.
        merged_metadata = {}
        for key in ("long_name", "standard_name", "name", "short_name", "units"):
            val = u_source.metadata(key)
            if val is not None:
                merged_metadata[key] = val
        if metadata:
            merged_metadata.update(metadata)
        # Rebuild a unified source so downstream code has a single object.
        source = get_source(
            u_source._data,
            x=x if x is not None else u_source.x.values,
            y=y if y is not None else u_source.y.values,
            u=u_arr,
            v=v_arr,
            context=context,
            units=units,
            u_units=u_units,
            v_units=v_units,
            x_units=x_units,
            y_units=y_units,
            metadata=merged_metadata or None,
        )
        u_values = source.u.values if source.u else None
        v_values = source.v.values if source.v else None

    else:
        raise ValueError("Vector plots accept at most two positional arguments (u_data, v_data).")

    return source, u_values, v_values


def _validate_uv_grids(u_source: Any, v_source: Any) -> None:
    """Raise ValueError when u and v are not defined on the same grid."""
    if not np.array_equal(u_source.x.values, v_source.x.values):
        raise ValueError(
            "X coordinates from u and v sources do not match. U and V components must be defined on the same grid."
        )
    if not np.array_equal(u_source.y.values, v_source.y.values):
        raise ValueError(
            "Y coordinates from u and v sources do not match. U and V components must be defined on the same grid."
        )


def extract_plottables_vector_2D(
    subplot: Any,
    method_name: str,
    args: tuple[Any, ...],
    x: str | np.ndarray | list[float] | None = None,
    y: str | np.ndarray | list[float] | None = None,
    u: str | np.ndarray | list[float] | None = None,
    v: str | np.ndarray | list[float] | None = None,
    style: Style | str | None = None,
    no_style: bool = False,
    units: str | None = None,
    u_units: str | None = None,
    v_units: str | None = None,
    x_units: str | None = None,
    y_units: str | None = None,
    extract_domain: bool = False,
    auto_style: bool = False,
    resample: Any | None = None,
    colors: bool = False,
    metadata: dict[str, Any] | None = None,
    **kwargs: Any,
) -> Any:
    """
    Extract and process data for vector plotting methods (quiver, barbs).

    Parameters
    ----------
    subplot:
        Target subplot instance.
    method_name:
        ``"quiver"`` or ``"barbs"``.
    args:
        Positional data arguments; see ``_resolve_vector_sources`` for the
        supported calling conventions.
    x, y:
        Coordinate specifications.
    u, v:
        U/V component specifications (variable names or arrays).
    style:
        Style object, ``"auto"``, a named-style string, or ``None``.
    no_style:
        When ``True``, bypass the Style object.
    units:
        Target units for the vector components.
    u_units, v_units:
        Component-specific unit overrides.
    x_units, y_units:
        Coordinate unit overrides.
    extract_domain:
        When ``True``, clip data to the subplot domain.
    auto_style:
        Deprecated; use ``style="auto"`` instead.
    resample:
        Resampling strategy applied to each component independently.
    colors:
        When ``True``, colour vectors by wind speed (magnitude).
    metadata:
        Extra metadata merged into the Source.

    Returns
    -------
    matplotlib artist
    """
    # Step 0: Normalise style/units.
    units, style = _prepare_style_and_units(style, units, auto_style)

    # Step 1: Resolve u/v sources for all calling conventions.
    context = _infer_plot_context(subplot, method_name)
    source, u_values_raw, v_values_raw = _resolve_vector_sources(
        args, x, y, u, v, context, units, u_units, v_units, x_units, y_units, metadata
    )

    # Step 1.5: Infer a sensible variable name for the vector field.
    # The source may carry long_name like "U component of wind" (single-arg path
    # with a u-only FieldList) or a list ["U component of wind", "V component of
    # wind"] (single-arg path with a combined FieldList). Strip the component
    # prefix to get a clean name like "wind".
    if "long_name" not in (metadata or {}):
        import re as _re

        existing_raw = source.metadata("long_name") or source.metadata("standard_name") or source.metadata("name") or ""
        # Unwrap lists: take the first element (the U-component name).
        if isinstance(existing_raw, list):
            existing = existing_raw[0] if existing_raw else ""
        else:
            existing = existing_raw
        # Strip "U/V component of " phrasing, e.g. "U component of wind" -> "wind"
        cleaned = _re.sub(r"\b[uv]\s+component\s+of\s+", "", existing, flags=_re.IGNORECASE).strip()
        if cleaned and cleaned.lower() != existing.lower():
            source._metadata_resolver.user_metadata["long_name"] = cleaned

    # Step 2: Inject subplot-level plot kwargs.
    kwargs.update(subplot._plot_kwargs(source))

    # Step 2.5: Auto-fit the map extent to the data when no domain is set.
    # Vector resampling calls subplot.ax.get_extent(), so the extent must be
    # established first.
    if subplot.domain is None and hasattr(subplot, "ax"):
        try:
            import cartopy.crs as _ccrs

            from earthkit.plots.geography import domains as _domains
            from earthkit.plots.geography.domains import force_minus_180_to_180

            x_ext = source.x.values.squeeze()
            y_ext = source.y.values.squeeze()
            if isinstance(source.crs, _ccrs._CylindricalProjection) and np.any(x_ext > 180):
                x_ext = force_minus_180_to_180(x_ext)
            domain = _domains.Domain.from_bbox(
                bbox=[x_ext.min(), x_ext.max(), y_ext.min(), y_ext.max()],
                source_crs=source.crs,
                target_crs=subplot.crs,
            )
            bbox_vals = list(domain.bbox)
            if None not in bbox_vals and all(np.isfinite(v) for v in bbox_vals if v is not None):
                subplot.domain = domain
                subplot.ax.set_extent(
                    subplot.domain.bbox.to_cartopy_bounds(),
                    subplot.domain.bbox.crs,
                )
        except Exception:
            pass

    # Step 3: Resolve the Style object.
    # Pass a copy so that configure_style's key-popping does not affect kwargs,
    # then strip the same style-specific keys from kwargs so they don't leak
    # into the matplotlib call (e.g. cmap="turbo" must not bypass the Style's
    # discretised colormap built from the magnitude data).
    style_kwargs = {**kwargs}
    if colors is not False:
        style_kwargs["colors"] = colors
    style = configure_style(method_name, style, source, units, auto_style, style_kwargs)

    from earthkit.plots.styles import _STYLE_KWARGS

    for _k in _STYLE_KWARGS:
        kwargs.pop(_k, None)
    # cmap is a user-friendly alias for colors; remove it too.
    kwargs.pop("cmap", None)

    # Step 4: Extract and normalise coordinate arrays.
    # Squeeze away any leading size-1 field-count dimension (single earthkit
    # Field wrapped into a FieldList), and normalise longitudes > 180° into
    # [-180, 180] so cartopy renders the vectors in the correct hemisphere.
    x_values = source.x.values.squeeze()
    y_values = source.y.values.squeeze()
    if np.any(x_values > 180):
        from earthkit.plots.geography.domains import (
            force_minus_180_to_180,
            roll_from_0_360_to_minus_180_180,
        )

        ref = x_values[0] if x_values.ndim == 2 else x_values
        roll_by = roll_from_0_360_to_minus_180_180(ref)
        if x_values.ndim == 2:
            x_values = np.roll(x_values, roll_by, axis=1)
            u_values_raw = np.roll(u_values_raw, roll_by, axis=1)
            v_values_raw = np.roll(v_values_raw, roll_by, axis=1)
        else:
            x_values = np.roll(x_values, roll_by)
            u_values_raw = np.roll(u_values_raw, roll_by)
            v_values_raw = np.roll(v_values_raw, roll_by)
        x_values = force_minus_180_to_180(x_values)

    if u_values_raw is None or v_values_raw is None:
        raise ValueError("Vector plots require u and v components.")

    u_values = u_values_raw
    v_values = v_values_raw

    # Step 7: Use style's resample setting when none was provided explicitly.
    if resample is None:
        resample = style.resample

    # Step 8: Clip to domain.
    if subplot.domain and extract_domain:
        x_values, y_values, _, [u_values, v_values] = subplot.domain.extract(
            x_values,
            y_values,
            extra_values=[u_values, v_values],
            source_crs=source.crs,
        )

    # Step 9: Apply resampling independently to u and v.
    if resample is not None:
        import cartopy.crs as ccrs

        from earthkit.plots.resample import Resample, Unstructured, _PixelSampler

        if isinstance(resample, _PixelSampler) and hasattr(subplot, "crs"):
            from earthkit.plots.resample.reproject import reproject_to_grid

            target_crs = subplot.crs or ccrs.PlateCarree()
            data_crs = source.crs or ccrs.PlateCarree()
            try:
                bbox_target = subplot.ax.get_extent(crs=target_crs)
            except Exception:
                bbox_target = (-180, 180, -90, 90)
            nx, ny = resample.resolve(bbox_target, crs=target_crs)

            # Extract 1-D axes from a regular meshgrid for the fast path.
            if x_values.ndim == 2 and y_values.ndim == 2:
                if np.allclose(x_values, x_values[0, :]) and np.allclose(y_values.T, y_values[:, 0]):
                    x_src, y_src = x_values[0, :], y_values[:, 0]
                else:
                    x_src, y_src = x_values, y_values
            else:
                x_src, y_src = x_values, y_values

            x_values, y_values, u_values = reproject_to_grid(
                x_src,
                y_src,
                u_values,
                crs_src=data_crs,
                bbox_target=bbox_target,
                crs_target=target_crs,
                nx=nx,
                ny=ny,
            )
            _, _, v_values = reproject_to_grid(
                x_src,
                y_src,
                v_values,
                crs_src=data_crs,
                bbox_target=bbox_target,
                crs_target=target_crs,
                nx=nx,
                ny=ny,
            )
            kwargs["transform"] = target_crs

        elif isinstance(resample, Unstructured):
            x_values, y_values, u_values = resample.apply(
                x_values,
                y_values,
                u_values,
                source_crs=source.crs,
                target_crs=subplot.crs,
            )
            _, _, v_values = resample.apply(
                x_values,
                y_values,
                v_values,
                source_crs=source.crs,
                target_crs=subplot.crs,
            )
        elif isinstance(resample, Resample):
            x_values, y_values, u_values, v_values = resample.apply(x_values, y_values, u_values, v_values)

    # Step 10: Build the argument list for the plotting method.
    plot_args = [x_values, y_values, u_values, v_values]

    # Optionally colour by wind speed (magnitude).
    if colors:
        magnitude = source.z.values if source.z else np.sqrt(u_values**2 + v_values**2)
        plot_args.append(magnitude)

    # Step 11: Render.
    mappable = getattr(style, method_name)(subplot.current_ax, *plot_args, **kwargs)

    # Step 12: Create the Layer.
    from earthkit.plots.components.layers import Layer

    subplot.layers.append(Layer(source, mappable, subplot, style))

    # Set axis labels from coordinate names when they were provided as strings.
    if isinstance(source._x_spec, str):
        subplot.current_ax.set_xlabel(source._x_spec)
    if isinstance(source._y_spec, str):
        subplot.current_ax.set_ylabel(source._y_spec)

    return mappable


# ---------------------------------------------------------------------------
# Envelope pipeline (fill_between, quantile bands, …)
# ---------------------------------------------------------------------------


def extract_plottables_envelope(
    subplot: Any,
    data: np.ndarray | list[float] | None = None,
    x: str | np.ndarray | list[float] | None = None,
    y: str | np.ndarray | list[float] | None = None,
    z: str | np.ndarray | list[float] | None = None,
    every: int | None = None,
    units: str | None = None,
    x_units: str | None = None,
    y_units: str | None = None,
    z_units: str | None = None,
    extract_domain: bool = False,
    **kwargs: Any,
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    """
    Extract coordinates for envelope plotting methods (fill_between, …).

    Unlike the other pipeline functions this one returns raw coordinate arrays
    rather than creating a Layer — the caller (a Subplot method) is responsible
    for the actual matplotlib call and Layer creation.

    Parameters
    ----------
    subplot:
        Target subplot instance.
    data:
        Main data array (may be ``None`` when x/y/z are provided separately).
    x, y, z:
        Coordinate/data specifications.
    every:
        Stride for data thinning.
    units:
        Target units for the primary data dimension.
    x_units, y_units, z_units:
        Dimension-specific unit overrides.
    extract_domain:
        When ``True``, clip data to the subplot domain.

    Returns
    -------
    (x_values, y_values, z_values)
        Where z_values may be ``None``.
    """
    source = get_source(
        data=data,
        x=x,
        y=y,
        z=z,
        context=PlotContext.CARTESIAN_2D,
        units=units,
        x_units=x_units,
        y_units=y_units,
        z_units=z_units,
    )

    kwargs = {**subplot._plot_kwargs(source), **kwargs}

    if (data is None and z is None) or (z is not None and not z):
        z_values = None
    elif source.z is not None:
        z_values = source.z.values
    else:
        z_values = None

    x_values = source.x.values
    y_values = source.y.values

    if every is not None:
        x_values = x_values[::every]
        y_values = y_values[::every]
        if z_values is not None:
            z_values = z_values[::every, ::every]

    if subplot.domain is not None and extract_domain:
        x_values, y_values, z_values = subplot.domain.extract(x_values, y_values, z_values, source_crs=source.crs)

    return x_values, y_values, z_values


# ---------------------------------------------------------------------------
# Subplot decorator factories
# ---------------------------------------------------------------------------


def plot_1D(method_name=None):
    import functools

    def decorator(method):
        @functools.wraps(method)
        def wrapper(
            self,
            *args,
            x=None,
            y=None,
            z=None,
            style=None,
            every=None,
            resample=False,
            colorby=None,
            dashby=None,
            markerby=None,
            sizeby=None,
            colors=None,
            dashes=None,
            markers=None,
            sizes=None,
            label=None,
            **kwargs,
        ):
            from itertools import product

            import numpy as np
            import pandas as pd
            import xarray as xr

            # Inject subplot-level fixed units if not already specified by the caller.
            if "x_units" not in kwargs and self._fixed_x_units is not None:
                kwargs["x_units"] = self._fixed_x_units
            if "y_units" not in kwargs and "units" not in kwargs and self._fixed_y_units is not None:
                kwargs["y_units"] = self._fixed_y_units

            # Accept underscore aliases (color_by → colorby, etc.)
            if colorby is None:
                colorby = kwargs.pop("color_by", None)
            if dashby is None:
                dashby = kwargs.pop("dash_by", None)
            if markerby is None:
                markerby = kwargs.pop("marker_by", None)
            if sizeby is None:
                sizeby = kwargs.pop("size_by", None)

            # Collect active *by dimensions: param_key → coordinate name
            by_dims = {
                k: v
                for k, v in [
                    ("colorby", colorby),
                    ("dashby", dashby),
                    ("markerby", markerby),
                    ("sizeby", sizeby),
                ]
                if v is not None
            }

            if not by_dims:
                # Default single-call path — no grouping requested
                extract_plottables_1D(
                    self,
                    method_name or method.__name__,
                    args=args,
                    x=x,
                    y=y,
                    z=z,
                    style=style,
                    every=every,
                    resample=resample,
                    label=label,
                    **kwargs,
                )
                return self if self._chainable else (self.layers[-1].mappable if self.layers else None)

            # Require xarray DataArray when any *by is set
            data = args[0] if args else None
            if not isinstance(data, xr.DataArray):
                raise TypeError(
                    "colorby/dashby/markerby/sizeby require a single xarray DataArray as the first positional argument."
                )
            rest_args = args[1:]

            # ------------------------------------------------------------------
            # Helpers
            # ------------------------------------------------------------------

            def _unique_vals(da, dim):
                """Unique values along *dim*, preserving numpy dtype for .sel()."""
                vals = da[dim].values
                seen = {}
                for v in vals.flat:
                    key = v.tobytes() if hasattr(v, "tobytes") else v
                    if key not in seen:
                        seen[key] = v
                return list(seen.values())

            def _to_python(val):
                """Convert numpy scalar to a Python-native value for formatting."""
                if isinstance(val, np.datetime64):
                    return pd.Timestamp(val)
                if hasattr(val, "item"):
                    return val.item()
                return val

            def _scalar_str(val):
                """Default human-readable string for a single value."""
                py_val = _to_python(val)
                if hasattr(py_val, "isoformat"):
                    return str(py_val)[:10]
                return str(py_val)

            def _make_label(combo):
                """Build legend label for a combination of *by values."""
                # Map coordinate name → python value, deduplicating repeated coords
                coord_vals = {}
                for dim_key, val in zip(dim_keys, combo):
                    coord = by_dims[dim_key]
                    if coord not in coord_vals:
                        coord_vals[coord] = _to_python(val)
                if label is not None:
                    return label.format(**coord_vals)
                # Default: join unique values with " / "
                return " / ".join(_scalar_str(v) for v in coord_vals.values())

            # ------------------------------------------------------------------
            # Build visual mappings for each *by dimension
            # list  → positional assignment (index order matches unique values)
            # dict  → explicit mapping (coord value string → visual value)
            # None  → use defaults
            # ------------------------------------------------------------------

            _DEFAULT_DASHES = ["solid", "dashed", "dotted", "dashdot"]
            _DEFAULT_MARKERS = ["o", "s", "^", "D", "v", "p", "X", "*"]

            from matplotlib import rcParams

            # Call _unique_vals ONCE per dimension so id() keys are stable
            # throughout the entire function.
            dim_keys = list(by_dims.keys())
            dim_unique = {dk: _unique_vals(data, by_dims[dk]) for dk in dim_keys}

            def _build_map(unique, user_values, default_fn):
                """Return {id(val): visual_value} for a *by dimension."""
                n = len(unique)
                if user_values is None:
                    vis_vals = [default_fn(i) for i in range(n)]
                elif isinstance(user_values, dict):
                    vis_vals = [user_values.get(str(_to_python(v)), default_fn(i)) for i, v in enumerate(unique)]
                else:
                    cycle = list(user_values)
                    vis_vals = [cycle[i % len(cycle)] for i in range(n)]
                return {id(v): vis for v, vis in zip(unique, vis_vals)}

            prop_cycle_colors = [p["color"] for p in rcParams["axes.prop_cycle"]]

            color_map = (
                _build_map(
                    dim_unique["colorby"],
                    colors,
                    lambda i: prop_cycle_colors[i % len(prop_cycle_colors)],
                )
                if colorby is not None
                else {}
            )
            dash_map = (
                _build_map(
                    dim_unique["dashby"],
                    dashes,
                    lambda i: _DEFAULT_DASHES[i % len(_DEFAULT_DASHES)],
                )
                if dashby is not None
                else {}
            )
            marker_map = (
                _build_map(
                    dim_unique["markerby"],
                    markers,
                    lambda i: _DEFAULT_MARKERS[i % len(_DEFAULT_MARKERS)],
                )
                if markerby is not None
                else {}
            )
            size_map = (
                _build_map(
                    dim_unique["sizeby"],
                    sizes,
                    lambda i: float(np.linspace(0.8, 2.0, max(len(dim_unique["sizeby"]), 1))[i]),
                )
                if sizeby is not None
                else {}
            )

            # ------------------------------------------------------------------
            # Iterate over the cartesian product of all *by dimensions
            # ------------------------------------------------------------------

            combos = list(product(*[dim_unique[dk] for dk in dim_keys]))

            seen_label_keys = set()

            for combo in combos:
                sel = {}
                call_kwargs = dict(kwargs)

                for dim_key, val in zip(dim_keys, combo):
                    coord = by_dims[dim_key]
                    sel[coord] = val
                    if dim_key == "colorby":
                        call_kwargs["color"] = color_map[id(val)]
                    elif dim_key == "dashby":
                        call_kwargs["linestyle"] = dash_map[id(val)]
                    elif dim_key == "markerby":
                        call_kwargs["marker"] = marker_map[id(val)]
                    elif dim_key == "sizeby":
                        call_kwargs["linewidth"] = size_map[id(val)]

                slice_da = data.sel(sel)

                # One legend entry per unique combination of *by coord values;
                # suppress duplicates (e.g. same coord used in colorby + dashby).
                label_key = tuple(
                    id(combo[i])
                    for i, dk in enumerate(dim_keys)
                    # deduplicate by coord name — only first occurrence counts
                    if by_dims[dk] not in [by_dims[dim_keys[j]] for j in range(i)]
                )
                if label_key not in seen_label_keys:
                    call_kwargs["label"] = _make_label(combo)
                    seen_label_keys.add(label_key)
                else:
                    call_kwargs["label"] = "_nolegend_"

                extract_plottables_1D(
                    self,
                    method_name or method.__name__,
                    args=(slice_da, *rest_args),
                    x=x,
                    y=y,
                    z=z,
                    style=style,
                    every=every,
                    resample=resample,
                    **call_kwargs,
                )

            return self if self._chainable else (self.layers[-1].mappable if self.layers else None)

        return wrapper

    return decorator


def plot_2D(method_name=None, extract_domain=False, default_resample=None):
    import functools

    from earthkit.plots.resample import _AUTO, Bilinear

    def decorator(method):
        @functools.wraps(method)
        def wrapper(
            self,
            *args,
            x=None,
            y=None,
            z=None,
            style=None,
            every=None,
            auto_style=False,
            resample=_AUTO,
            **kwargs,
        ):
            if resample is _AUTO:
                if default_resample is False:
                    resample = False
                # else: keep _AUTO — the pipeline will resolve it
            elif resample is True:
                resample = Bilinear()
            elif isinstance(resample, list):
                from earthkit.plots.resample import Chain

                resample = Chain(resample)
            extract_plottables_2D(
                subplot=self,
                method_name=method_name or method.__name__,
                args=args,
                x=x,
                y=y,
                z=z,
                style=style,
                every=every,
                auto_style=auto_style,
                extract_domain=extract_domain,
                resample=resample,
                **kwargs,
            )
            return self if self._chainable else (self.layers[-1].mappable if self.layers else None)

        return wrapper

    return decorator


def plot_vector(method_name=None, extract_domain=False):
    import functools

    from earthkit.plots.resample import Bilinear

    def decorator(method):
        @functools.wraps(method)
        def wrapper(
            self,
            *args,
            x=None,
            y=None,
            u=None,
            v=None,
            colors=False,
            style=None,
            units=None,
            auto_style=False,
            resample=Bilinear(40),
            **kwargs,
        ):
            extract_plottables_vector_2D(
                subplot=self,
                method_name=method_name or method.__name__,
                args=args,
                x=x,
                y=y,
                u=u,
                v=v,
                style=style,
                units=units,
                auto_style=auto_style,
                extract_domain=extract_domain,
                resample=resample,
                colors=colors,
                **kwargs,
            )
            return self if self._chainable else (self.layers[-1].mappable if self.layers else None)

        return wrapper

    return decorator
