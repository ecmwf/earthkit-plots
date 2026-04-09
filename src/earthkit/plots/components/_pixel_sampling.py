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
Pixel-space and data-space resampling for the plotting pipeline.

This module owns two related but distinct resampling concerns:

Data-space resampling  (``_apply_data_resampling``)
    Operates on raw coordinate arrays *before* they are handed to matplotlib.
    Handles ``Regrid``, ``Unstructured``, and generic ``Resample`` steps.
    Does *not* require subplot/CRS/bbox context.

Pixel-space resampling  (``_apply_pixel_sampling``)
    Projects data onto the *target projection's pixel grid* using
    ``Bilinear`` or ``NearestNeighbour`` interpolation.  Requires
    subplot/CRS/bbox context and is therefore deferred to render time.

The ``_auto_resample_policy`` function encodes the single source of truth
for what ``resample='auto'`` means for each (method, grid_type) combination.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from earthkit.plots.styles import Style


# ---------------------------------------------------------------------------
# Auto-resample policy
# ---------------------------------------------------------------------------
# Edit this table to change what resample="auto" resolves to for any
# (method_name, grid_type) combination.  method_name is matched by prefix.
# ---------------------------------------------------------------------------


def _auto_resample_policy(
    method_name: str,
    is_structured: bool,
    is_unstructured: bool = False,
) -> Any:
    """
    Return the resample object to use when ``resample='auto'``.

    Auto-resample policy table
    --------------------------

    +--------------------------+-------------------+----------------------------------+
    | Method                   | Grid type         | Auto resample                    |
    +==========================+===================+==================================+
    | contour / contourf       | structured        | Chain(Regrid(), Bilinear())      |
    +--------------------------+-------------------+----------------------------------+
    | contour / contourf       | unstructured      | Unstructured()                   |
    +--------------------------+-------------------+----------------------------------+
    | contour / contourf       | regular           | Bilinear()                       |
    +--------------------------+-------------------+----------------------------------+
    | pcolormesh               | structured        | error — must be explicit         |
    +--------------------------+-------------------+----------------------------------+
    | pcolormesh               | unstructured      | Unstructured()                   |
    +--------------------------+-------------------+----------------------------------+
    | pcolormesh               | regular           | False (native pcolormesh)        |
    +--------------------------+-------------------+----------------------------------+

    Parameters
    ----------
    method_name:
        The name of the plotting method (e.g. ``"contourf"``, ``"pcolormesh"``).
    is_structured:
        Whether the source data is on a structured grid (HEALPix / reduced
        Gaussian).
    is_unstructured:
        Whether the source data is scattered/unstructured (not regular
        rectilinear and not HEALPix / reduced Gaussian).

    Returns
    -------
    Resample | False
        The resolved resample object, or ``False`` to skip resampling.

    Raises
    ------
    ValueError
        When the method/grid combination is explicitly unsupported.
    """
    from earthkit.plots.resample import Bilinear, Chain, Regrid, Unstructured

    is_contour = method_name.startswith("contour")
    is_pcolormesh = method_name == "pcolormesh"

    if is_contour:
        if is_structured:
            # Regrid to a regular lat/lon grid first, then pixel-sample onto
            # the target projection for smooth rendering.
            return Chain(Regrid(), Bilinear())
        if is_unstructured:
            return Unstructured()
        return Bilinear()

    if is_pcolormesh:
        if is_structured:
            raise ValueError(
                "pcolormesh cannot render structured grid data (HEALPix / reduced "
                "Gaussian / ORCA) with resample='auto'.  Pass an explicit resample "
                "strategy, e.g. resample=Regrid() to convert to a regular grid first, "
                "or use grid_cells() for automatic nearest-neighbour cell rendering."
            )
        if is_unstructured:
            return Unstructured()
        # Regular grid: pcolormesh renders natively via transform=PlateCarree().
        return False

    # All other methods: no resampling.
    return False


# ---------------------------------------------------------------------------
# Data-space resampling
# ---------------------------------------------------------------------------


def _apply_data_resampling(
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray | None,
    resample: Any,
    source: Any,
    subplot: Any,
    method_name: str,
    *,
    allow_pixel_samplers: bool = True,
    kwargs: dict | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None, bool]:
    """
    Apply data-space resampling steps to ``(x, y, z)`` coordinate arrays.

    Handles ``Chain``, ``Regrid``, ``Unstructured``, and generic ``Resample``
    steps.  Pixel-samplers (``_PixelSampler`` subclasses such as ``Bilinear``
    and ``NearestNeighbour``) need subplot/CRS/bbox context that is not
    available here; they are handled later by ``_apply_pixel_sampling``.

    Parameters
    ----------
    x, y, z:
        Coordinate and data arrays to resample.
    resample:
        The resample object to apply.  ``False`` and ``None`` are no-ops.
    source:
        The data source; used for ``gridspec`` and ``crs``.
    subplot:
        The subplot instance; used for ``crs`` on geographic plots.
    method_name:
        The plotting method name; forwarded to context inference when a
        ``Regrid`` step is present.
    allow_pixel_samplers:
        When ``False`` (1D / scatter context), raise ``ValueError`` if a
        pixel-sampler step is encountered.  When ``True`` (2D context),
        pixel steps are silently skipped here (applied later in
        ``_apply_pixel_sampling``).
    kwargs:
        The live ``kwargs`` dict forwarded from the caller.  Modified
        in-place when an ``Unstructured`` step pops ``transform`` /
        ``transform_first`` keys.

    Returns
    -------
    (x, y, z, extract_domain_suppressed)
        Resampled arrays plus a flag indicating whether an ``Unstructured``
        step has already clipped to the target CRS (so the caller should
        skip the normal domain-extraction step).
    """
    if resample is False or resample is None:
        return x, y, z, False

    # Lazily imported here to avoid a circular dependency at module level.
    from earthkit.plots.components._pipeline import _infer_plot_context
    from earthkit.plots.resample import (
        Chain,
        Regrid,
        Resample,
        Unstructured,
        _PixelSampler,
    )

    extract_domain_suppressed = False

    if isinstance(resample, Chain):
        if not allow_pixel_samplers and resample.pixel_step is not None:
            raise ValueError(
                f"{resample.pixel_step.__class__.__name__} is a pixel-sampler and "
                "cannot be used with scatter (it produces a regular image grid, not "
                "discrete points).  Use Regrid() to resample to a regular lat/lon "
                "grid before scattering, e.g. resample=Regrid()."
            )
        data_steps = resample.data_steps
    elif isinstance(resample, _PixelSampler):
        if not allow_pixel_samplers:
            raise ValueError(
                f"{resample.__class__.__name__} is a pixel-sampler and cannot be "
                "used with scatter (it produces a regular image grid, not discrete "
                "points).  Use Regrid() to resample to a regular lat/lon grid "
                "before scattering, e.g. resample=Regrid()."
            )
        # In the 2D context pixel-samplers are deferred to _apply_pixel_sampling.
        data_steps = []
    else:
        data_steps = [resample]

    for step in data_steps:
        if isinstance(step, Regrid):
            context = _infer_plot_context(subplot, method_name)
            x, y, z = step.apply(x, y, z, gridspec=source.gridspec, context=context)
        elif isinstance(step, Unstructured):
            x, y, z = step.apply(
                x,
                y,
                z,
                source_crs=source.crs,
                target_crs=getattr(subplot, "crs", None),
            )
            if step.transform:
                if kwargs is not None:
                    kwargs.pop("transform", None)
                    kwargs.pop("transform_first", None)
                extract_domain_suppressed = True
        elif isinstance(step, Resample):
            x, y, z = step.apply(x, y, z)

    return x, y, z, extract_domain_suppressed


# ---------------------------------------------------------------------------
# Pixel-space resampling result
# ---------------------------------------------------------------------------


class PixelSamplingResult:
    """
    Return value of :func:`_apply_pixel_sampling`.

    Attributes
    ----------
    x, y, z:
        Coordinate and data arrays after sampling (may equal the inputs when
        no sampling was performed).
    reprojected:
        ``True`` when the data were projected onto the target CRS grid.
        The caller should suppress cyclic-point wrapping and skip the normal
        plot call when this is ``True``.
    mappable:
        Pre-rendered artist produced by the NearestNeighbour ``imshow`` path.
        ``None`` for all other paths; the caller must render the plot itself.
    """

    __slots__ = ("x", "y", "z", "reprojected", "mappable")

    def __init__(
        self,
        x: np.ndarray,
        y: np.ndarray,
        z: np.ndarray | None,
        *,
        reprojected: bool = False,
        mappable: Any = None,
    ):
        self.x = x
        self.y = y
        self.z = z
        self.reprojected = reprojected
        self.mappable = mappable


# ---------------------------------------------------------------------------
# Pixel-space resampling implementation
# ---------------------------------------------------------------------------


def _get_subplot_bbox(
    subplot: Any,
    target_crs: Any,
) -> tuple[float, float, float, float]:
    """Return the bounding box of *subplot* in *target_crs* coordinates."""
    try:
        return subplot.ax.get_extent(crs=target_crs)
    except AttributeError:
        if subplot.domain is not None:
            return subplot.domain.bbox.to_cartopy_bounds()
        return (-180, 180, -90, 90)


def _try_nearest_neighbour_imshow(
    subplot: Any,
    x_values: np.ndarray,
    y_values: np.ndarray,
    z_values: np.ndarray,
    *,
    data_crs: Any,
    bbox_target: tuple,
    target_crs: Any,
    nx: int,
    ny: int,
    style: Style | None,
    kwargs: dict,
) -> PixelSamplingResult | None:
    """
    Attempt the NearestNeighbour fast-path via ``ax.imshow``.

    Only works for regular rectilinear grids (rows and columns are constant).
    Returns a :class:`PixelSamplingResult` with the pre-rendered mappable on
    success, or ``None`` when the grid is curvilinear (caller should fall back
    to the Bilinear path).
    """
    is_regular = (
        x_values.ndim == 2
        and y_values.ndim == 2
        and np.allclose(x_values, x_values[0, :])
        and np.allclose(y_values.T, y_values[:, 0])
    )
    if not is_regular:
        return None

    from earthkit.plots.resample.reproject import _reproject_nn

    image, extent = _reproject_nn(
        x_values[0, :],
        y_values[:, 0],
        z_values,
        crs_src=data_crs,
        bbox_target=bbox_target,
        crs_target=target_crs,
        nx=nx,
        ny=ny,
    )
    plot_kwargs = dict(kwargs)
    if style is not None:
        plot_kwargs.update(style.to_pcolormesh_kwargs(image))
    plot_kwargs.pop("transform", None)
    plot_kwargs.pop("transform_first", None)
    plot_kwargs.setdefault("interpolation", "nearest")
    mappable = subplot.ax.imshow(image, extent=extent, origin="lower", **plot_kwargs)
    return PixelSamplingResult(x_values, y_values, z_values, reprojected=True, mappable=mappable)


def _reproject_bilinear(
    x_values: np.ndarray,
    y_values: np.ndarray,
    z_values: np.ndarray,
    *,
    data_crs: Any,
    bbox_target: tuple,
    target_crs: Any,
    nx: int,
    ny: int,
    use_nearest: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Reproject data onto a regular pixel grid using bilinear (or nearest) interpolation.

    For 2-D regular meshgrids the 1-D axis vectors are extracted and passed to
    :func:`~earthkit.plots.resample.reproject.reproject_to_grid`, which uses a
    fast ``RegularGridInterpolator``.  Curvilinear (2-D) and scattered (1-D)
    grids are passed through directly, triggering the scattered-interpolation
    path inside ``reproject_to_grid``.
    """
    from earthkit.plots.resample.reproject import reproject_to_grid

    # Unwrap regular meshgrids to 1-D axis vectors for the fast path.
    if x_values.ndim == 2 and y_values.ndim == 2:
        if np.allclose(x_values, x_values[0, :]) and np.allclose(y_values.T, y_values[:, 0]):
            x_src = x_values[0, :]
            y_src = y_values[:, 0]
        else:
            x_src = x_values  # curvilinear — use scattered path
            y_src = y_values
    else:
        x_src = x_values
        y_src = y_values

    return reproject_to_grid(
        x_src,
        y_src,
        z_values,
        crs_src=data_crs,
        bbox_target=bbox_target,
        crs_target=target_crs,
        nx=nx,
        ny=ny,
        method="nearest" if use_nearest else "linear",
    )


def _apply_pixel_sampling(
    subplot: Any,
    source: Any,
    x_values: np.ndarray,
    y_values: np.ndarray,
    z_values: np.ndarray | None,
    *,
    resample: Any,
    method_name: str,
    no_style: bool,
    style: Style | None,
    data_crs: Any,
    kwargs: dict,
) -> PixelSamplingResult:
    """
    Apply pixel-space resampling (Bilinear / NearestNeighbour) to the data.

    Unlike the data-space resamplers handled by :func:`_apply_data_resampling`,
    pixel samplers operate in the *target projection's pixel grid* and therefore
    need subplot/CRS/bbox context that is only available at render time.

    This function is a no-op (returns inputs unchanged) when:

    * *resample* carries no pixel-sampler step.
    * *no_style* is ``True`` (raw matplotlib path skips reprojection).
    * *method_name* is not a contour or pcolormesh variant.
    * The subplot has no ``crs`` attribute (non-geographic axes).
    * Source and target CRS are the same *and* the data is not scattered.

    Parameters
    ----------
    subplot:
        The target subplot; must expose ``crs`` and ``ax`` for geographic plots.
    source:
        The data source; used to fall back to ``source.crs`` when *data_crs*
        is ``None`` and to access ``domain``.
    x_values, y_values, z_values:
        Coordinate and data arrays from the preceding pipeline steps.
    resample:
        The active resample object (``Chain``, ``_PixelSampler``, or any
        other value — the latter is treated as "no pixel sampler").
    method_name:
        Name of the plotting method (e.g. ``"contourf"``, ``"pcolormesh"``).
    no_style:
        When ``True`` the raw matplotlib path is used; pixel sampling is skipped.
    style:
        The active :class:`~earthkit.plots.styles.Style`; used only by the
        NearestNeighbour ``imshow`` path.
    data_crs:
        CRS of the source data.  May be ``None`` for plain lat/lon data; the
        function falls back to ``cartopy.crs.PlateCarree()`` in that case.
    kwargs:
        Live kwargs dict from the caller.  Modified in-place when the
        Bilinear path sets ``kwargs["transform"]``.

    Returns
    -------
    PixelSamplingResult
    """
    from earthkit.plots.resample import Chain, NearestNeighbour, _PixelSampler

    # Resolve the effective pixel sampler from a plain sampler or a Chain.
    if isinstance(resample, Chain):
        pixel_sampler = resample.pixel_step
    elif isinstance(resample, _PixelSampler):
        pixel_sampler = resample
    else:
        pixel_sampler = None

    supports_pixel_sampling = method_name.startswith("contour") or method_name == "pcolormesh"
    if pixel_sampler is None or no_style or not supports_pixel_sampling or not hasattr(subplot, "crs"):
        return PixelSamplingResult(x_values, y_values, z_values)

    import cartopy.crs as ccrs

    target_crs = subplot.crs
    resolved_data_crs = data_crs or ccrs.PlateCarree()

    # Only reproject when the CRS differs OR the data is scattered (1-D arrays).
    is_scattered = x_values.ndim == 1 and z_values is not None and z_values.ndim == 1
    crs_differs = type(resolved_data_crs).__name__ != type(target_crs).__name__
    if target_crs is None or (not crs_differs and not is_scattered):
        return PixelSamplingResult(x_values, y_values, z_values)

    bbox_target = _get_subplot_bbox(subplot, target_crs)
    nx, ny = pixel_sampler.resolve(bbox_target, crs=target_crs)

    # NearestNeighbour path: renders via imshow for regular rectilinear grids.
    if isinstance(pixel_sampler, NearestNeighbour):
        nn_result = _try_nearest_neighbour_imshow(
            subplot,
            x_values,
            y_values,
            z_values,
            data_crs=resolved_data_crs,
            bbox_target=bbox_target,
            target_crs=target_crs,
            nx=nx,
            ny=ny,
            style=style,
            kwargs=kwargs,
        )
        if nn_result is not None:
            return nn_result
        # Curvilinear grid — fall through to the Bilinear path below.

    # Bilinear path (also the NearestNeighbour fallback for curvilinear grids).
    x_values, y_values, z_values = _reproject_bilinear(
        x_values,
        y_values,
        z_values,
        data_crs=resolved_data_crs,
        bbox_target=bbox_target,
        target_crs=target_crs,
        nx=nx,
        ny=ny,
        use_nearest=isinstance(pixel_sampler, NearestNeighbour),
    )
    kwargs["transform"] = target_crs
    return PixelSamplingResult(x_values, y_values, z_values, reprojected=True)
