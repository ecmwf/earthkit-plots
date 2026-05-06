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

import numpy as np

from earthkit.plots.resample._base import Resample

# Hard limit on the total number of pixels a _PixelSampler may produce.
# Exceeding this in resolution mode triggers a warning and automatic clamping
# rather than silently allocating a multi-GB array.
# 16 MP (~4000 × 4000) is generous for screen rendering and safe on all machines.
_MAX_PIXELS = 16_000_000


class _PixelSampler(Resample):
    """
    Base class for pixel-sampling resamplers (``Bilinear``, ``NearestNeighbour``).

    Handles the shared ``nx``/``ny``/``resolution`` specification and the
    :meth:`resolve` method that converts them to a concrete pixel count for a
    given bounding box.  Subclasses implement the actual sampling logic and are
    the public API.

    The output grid can be specified in three ways:

    - **Fixed pixel count** (``nx``/``ny``): always produces exactly that many
      pixels regardless of the map extent.
    - **Fixed resolution** (``resolution``): the pixel spacing is fixed in the
      target CRS units (degrees for PlateCarree, metres for projected CRS), so
      the pixel count adapts to the map extent.
    - **Auto** (``nx="auto"`` / ``ny="auto"``): the pixel count is chosen as
      ``min(source_grid_size, subplot_pixels, DEFAULT_NX/NY)`` — no finer than
      the source data or the display can show.

    Use the :meth:`at_resolution` class method as a named constructor when
    specifying a resolution is more natural than a pixel count.

    Parameters
    ----------
    nx : int or ``"auto"``, optional
        Number of pixels in the x direction.  Pass ``"auto"`` to let
        earthkit-plots choose based on data resolution and subplot pixel width.
        Mutually exclusive with ``resolution``.  Defaults to 1000 when neither
        is given.
    ny : int or ``"auto"``, optional
        Number of pixels in the y direction.  Pass ``"auto"`` to let
        earthkit-plots choose based on data resolution and subplot pixel height.
        Mutually exclusive with ``resolution``.  Defaults to 1000 when neither
        is given.
    resolution : float or tuple of float, optional
        Pixel spacing in target CRS units (e.g. degrees or metres).  A single
        value sets the same spacing in both directions; a 2-tuple sets
        ``(dx, dy)`` separately.  Mutually exclusive with ``nx``/``ny``.
    """

    DEFAULT_NX = 1000
    DEFAULT_NY = 1000

    def __init__(self, *args, nx=None, ny=None, resolution=None):
        if args:
            if nx is not None or ny is not None or resolution is not None:
                raise ValueError(
                    f"{self.__class__.__name__} can take positional arguments or "
                    "keyword arguments, but not a combination of both."
                )
            if len(args) == 1:
                if args[0] == "auto":
                    nx = ny = "auto"
                else:
                    nx = ny = int(args[0])
            elif len(args) == 2:
                nx = "auto" if args[0] == "auto" else int(args[0])
                ny = "auto" if args[1] == "auto" else int(args[1])
            else:
                raise ValueError(
                    f"{self.__class__.__name__} accepts at most 2 positional arguments (nx, ny); received {len(args)}."
                )

        if resolution is not None and (nx is not None or ny is not None):
            raise ValueError(f"{self.__class__.__name__}: 'resolution' is mutually exclusive with 'nx'/'ny'.")
        if resolution is not None:
            if isinstance(resolution, (tuple, list)):
                self._dx, self._dy = float(resolution[0]), float(resolution[1])
            else:
                self._dx = self._dy = float(resolution)
            self._resolution_mode = True
            self._auto_nx = False
            self._auto_ny = False
            self.nx = None
            self.ny = None
        else:
            self._dx = self._dy = None
            self._resolution_mode = False
            self._auto_nx = nx == "auto"
            self._auto_ny = ny == "auto"
            self.nx = None if self._auto_nx else (nx if nx is not None else self.DEFAULT_NX)
            self.ny = None if self._auto_ny else (ny if ny is not None else self.DEFAULT_NY)

    @classmethod
    def at_resolution(cls, dx, dy=None):
        """
        Create a sampler with a fixed pixel spacing in **degrees**.

        The resolution is always specified in degrees, regardless of the target
        map projection.  At render time :meth:`resolve` converts the degree
        spacing to the appropriate number of pixels for the current map extent,
        accounting for projected (metre-based) CRS automatically.

        Parameters
        ----------
        dx : float
            Pixel spacing in the x direction, in **degrees**.
        dy : float, optional
            Pixel spacing in the y direction, in **degrees**.
            If omitted, ``dy = dx`` (square pixels).

        Returns
        -------
        _PixelSampler subclass instance

        Examples
        --------
        >>> Bilinear.at_resolution(1.0)  # 1° × 1° pixels
        >>> NearestNeighbour.at_resolution(0.25)  # quarter-degree pixels
        >>> Bilinear.at_resolution(0.5, 1.0)  # 0.5° × 1° pixels
        """
        if dy is None:
            dy = dx
        return cls(resolution=(float(dx), float(dy)))

    @property
    def is_auto(self):
        """True when either axis is in auto mode."""
        return self._auto_nx or self._auto_ny

    def resolve(self, bbox, crs=None):
        """
        Return the concrete ``(nx, ny)`` for the given bounding box.

        For fixed-count and resolution modes this is cheap and stateless.
        For auto-mode axes, falls back to :meth:`resolve_auto` with no data or
        axes context, which applies only the default cap — pass data and axes
        via :meth:`resolve_auto` directly for the full adaptive behaviour.

        Parameters
        ----------
        bbox : tuple
            ``(xmin, xmax, ymin, ymax)`` in the target CRS units.
        crs : cartopy CRS, optional
            The target map CRS.  When provided and the CRS is not
            PlateCarree (i.e. the bbox units are not degrees), the stored
            degree resolution is converted to CRS units so that the pixel
            count is correct for projected maps.

        Returns
        -------
        nx, ny : int
        """
        if not self._resolution_mode:
            if self._auto_nx or self._auto_ny:
                # No data/axes context here — fall back to the default cap only.
                return self.resolve_auto(bbox, crs, x_values=None, y_values=None, ax=None)
            return self.nx, self.ny

        dx_crs, dy_crs = self._dx, self._dy  # stored in degrees

        if crs is not None:
            import cartopy.crs as ccrs

            if not isinstance(crs, ccrs.PlateCarree):
                # Convert degree resolution to CRS units by measuring the
                # projected length of one degree at the centre of the bbox.
                xmin, xmax, ymin, ymax = bbox
                cx = (xmin + xmax) / 2.0
                cy = (ymin + ymax) / 2.0
                plate = ccrs.PlateCarree()
                # Project two points 1° apart in x and y from the bbox centre
                # back into geographic coords, then forward into the target CRS
                try:
                    # geographic centre of the bbox
                    lon_c, lat_c, _ = plate.transform_points(crs, np.array([cx]), np.array([cy]))[0]
                    # one degree east and one degree north
                    pt_east = crs.transform_points(
                        plate,
                        np.array([lon_c + 1.0]),
                        np.array([lat_c]),
                    )[0]
                    pt_north = crs.transform_points(
                        plate,
                        np.array([lon_c]),
                        np.array([lat_c + 1.0]),
                    )[0]
                    metres_per_deg_x = abs(pt_east[0] - cx)
                    metres_per_deg_y = abs(pt_north[1] - cy)
                    if metres_per_deg_x > 0 and metres_per_deg_y > 0:
                        dx_crs = self._dx * metres_per_deg_x
                        dy_crs = self._dy * metres_per_deg_y
                except Exception:
                    pass  # fall back to raw degree values

        xmin, xmax, ymin, ymax = bbox
        nx = max(1, round(abs(xmax - xmin) / dx_crs))
        ny = max(1, round(abs(ymax - ymin) / dy_crs))

        total = nx * ny
        if total > _MAX_PIXELS:
            import warnings

            scale = (total / _MAX_PIXELS) ** 0.5
            nx_safe = max(1, round(nx / scale))
            ny_safe = max(1, round(ny / scale))
            warnings.warn(
                f"{self.__class__.__name__}.at_resolution({self._dx!r}) would produce a "
                f"{nx:,} × {ny:,} = {total:,} pixel grid, which exceeds the safety "
                f"limit of {_MAX_PIXELS:,} pixels.  Clamping to {nx_safe:,} × {ny_safe:,}. "
                "Pass nx/ny directly to suppress this warning and override the limit.",
                RuntimeWarning,
                stacklevel=4,
            )
            nx, ny = nx_safe, ny_safe

        return nx, ny

    def resolve_auto(self, bbox, crs, x_values, y_values, ax=None):
        """
        Return ``(nx, ny)`` for auto-mode axes, bounded by data and pixel resolution.

        For each axis marked ``"auto"``, the target pixel count is:

            min(source_grid_size - 1, subplot_pixels, DEFAULT_NX/NY)

        The ``- 1`` guard is a workaround for a pre-existing bug in
        ``reproject_to_grid`` where internal coordinate deduplication (e.g.
        removing the repeated ±180° longitude) shrinks the source but the
        reshape still uses the original size, causing a mismatch when the
        output grid matches the source exactly.
        TODO: fix the reshape in ``reproject.reproject_to_grid`` to use the
        post-dedup sizes, then remove the ``- 1`` here.

        Source coordinates are counted across the full arrays rather than
        filtering to the visible bbox.  The coordinates are in the source
        (data) CRS, which may differ from the target CRS that bbox is
        expressed in, making bbox-filtering unreliable.  For regional plots
        this slightly overcounts the visible data density, but the subplot
        pixel cap remains the binding constraint in those cases anyway.

        Axes with a fixed count are returned unchanged.  When ``x_values`` is
        ``None`` (called from :meth:`resolve` without data context), the data
        cap is skipped and only ``DEFAULT_NX/NY`` and the axes pixel cap apply.

        Parameters
        ----------
        bbox : tuple
            ``(xmin, xmax, ymin, ymax)`` in the target CRS units.
            Reserved for future domain-filtering; not currently used.
        crs : cartopy CRS
            The target map CRS.
            Reserved for future domain-filtering; not currently used.
        x_values, y_values : np.ndarray or None
            Source coordinate arrays (1-D or 2-D).  Pass ``None`` to skip the
            data resolution cap.
        ax : matplotlib Axes, optional
            The subplot axes; used to read the pixel dimensions of the plot area.
            When ``None`` the pixel cap is skipped.

        Returns
        -------
        nx, ny : int
        """
        # --- data resolution cap -------------------------------------------
        # Use shape rather than np.unique to avoid an O(n log n) sort copy.
        # For 1-D scattered data total length ≈ unique count; for 2-D grids
        # the axis lengths are exact.  Subtract one to guard against the
        # dedup/reshape mismatch described in the docstring above.
        if x_values is not None:
            if x_values.ndim == 2:
                data_nx = max(x_values.shape[1] - 1, 2)
                data_ny = max(x_values.shape[0] - 1, 2)
            else:
                data_nx = max(x_values.shape[0] - 1, 2)
                data_ny = max(y_values.shape[0] - 1, 2)
        else:
            data_nx = data_ny = None

        # --- pixel resolution cap ------------------------------------------
        ax_px_width = ax_px_height = None
        if ax is not None:
            try:
                fig = ax.get_figure()
                renderer = fig.canvas.get_renderer()
                bb = ax.get_window_extent(renderer=renderer)
                ax_px_width = max(1, int(bb.width))
                ax_px_height = max(1, int(bb.height))
            except Exception:
                # Pre-draw or headless — fall back to figsize × dpi estimate.
                try:
                    fig = ax.get_figure()
                    fw_px = fig.get_figwidth() * fig.dpi
                    fh_px = fig.get_figheight() * fig.dpi
                    pos = ax.get_position()  # fractional Axes position on figure
                    ax_px_width = max(1, int(fw_px * pos.width))
                    ax_px_height = max(1, int(fh_px * pos.height))
                except Exception:
                    pass

        def _cap(data_n, ax_px, default):
            caps = [default]
            if data_n is not None:
                caps.append(data_n)
            if ax_px is not None:
                caps.append(ax_px)
            return max(2, min(caps))

        nx = _cap(data_nx, ax_px_width, self.DEFAULT_NX) if self._auto_nx else self.nx
        ny = _cap(data_ny, ax_px_height, self.DEFAULT_NY) if self._auto_ny else self.ny
        return nx, ny

    def apply(self, *args, **kwargs):
        raise NotImplementedError(
            f"{self.__class__.__name__} is a rendering hint; it is handled internally during plotting."
        )

    def _repr_size(self):
        if self._resolution_mode:
            if self._dx == self._dy:
                return f"resolution={self._dx}"
            return f"resolution=({self._dx}, {self._dy})"
        nx_str = "'auto'" if self._auto_nx else str(self.nx)
        ny_str = "'auto'" if self._auto_ny else str(self.ny)
        return f"nx={nx_str}, ny={ny_str}"

    def __repr__(self):
        return f"{self.__class__.__name__}({self._repr_size()})"


class Bilinear(_PixelSampler):
    """
    Resample data onto a pixel grid using bilinear interpolation.

    For each pixel in an ``nx``-by-``ny`` output image covering the map extent,
    the value is computed by bilinear interpolation from the source grid using
    :class:`scipy.interpolate.RegularGridInterpolator`.  This produces smooth
    output but blurs sharp boundaries between grid cells.

    The output grid can be specified in two ways:

    - **Fixed pixel count** (``nx``/``ny``): always produces exactly that many
      pixels regardless of the map extent.
    - **Fixed resolution** (``resolution``): the pixel spacing is fixed in the
      target CRS units (degrees for PlateCarree, metres for projected CRS), so
      the pixel count adapts to the map extent.

    Parameters
    ----------
    nx : int or ``"auto"``, optional
        Number of pixels in the x direction.  Pass ``"auto"`` to let
        earthkit-plots choose based on data resolution and subplot pixel width.
        Mutually exclusive with ``resolution``.  Defaults to 1000 when neither
        is given.
    ny : int or ``"auto"``, optional
        Number of pixels in the y direction.  Pass ``"auto"`` to let
        earthkit-plots choose based on data resolution and subplot pixel height.
        Mutually exclusive with ``resolution``.  Defaults to 1000 when neither
        is given.
    resolution : float or tuple of float, optional
        Pixel spacing in target CRS units (e.g. degrees or metres).  A single
        value sets the same spacing in both directions; a 2-tuple sets
        ``(dx, dy)`` separately.  Mutually exclusive with ``nx``/``ny``.

    Examples
    --------
    >>> Bilinear()  # 1000 × 1000 pixels
    >>> Bilinear("auto")  # automatically sized to data and subplot
    >>> Bilinear(nx="auto", ny=500)  # auto x, fixed y
    >>> Bilinear(nx=2000, ny=1000)  # fixed pixel count
    >>> Bilinear(resolution=1.0)  # 1-degree pixels (PlateCarree)
    >>> Bilinear(resolution=(1.0, 0.5))  # 1° × 0.5° pixels
    """


class NearestNeighbour(_PixelSampler):
    """
    Resample data onto a pixel grid by nearest-neighbour cell lookup.

    For each pixel in an ``nx``-by-``ny`` output image covering the map extent,
    the pixel centre is back-transformed to the source CRS and the nearest
    source cell is found via :func:`numpy.searchsorted` on the 1-D source axes.
    This is O(nx×ny), preserves exact grid-cell boundaries with no blurring,
    and is equivalent to the approach used by the HEALPix and octahedral
    ``nnshow`` backends.

    Only valid for regular rectilinear source grids.  Curvilinear grids fall
    back to :class:`Bilinear` automatically.

    The output grid can be specified in two ways:

    - **Fixed pixel count** (``nx``/``ny``): always produces exactly that many
      pixels regardless of the map extent.
    - **Fixed resolution** (``resolution``): the pixel spacing is fixed in the
      target CRS units (degrees for PlateCarree, metres for projected CRS), so
      the pixel count adapts to the map extent.

    Parameters
    ----------
    nx : int or ``"auto"``, optional
        Number of pixels in the x direction.  Pass ``"auto"`` to let
        earthkit-plots choose based on data resolution and subplot pixel width.
        Mutually exclusive with ``resolution``.  Defaults to 1000 when neither
        is given.
    ny : int or ``"auto"``, optional
        Number of pixels in the y direction.  Pass ``"auto"`` to let
        earthkit-plots choose based on data resolution and subplot pixel height.
        Mutually exclusive with ``resolution``.  Defaults to 1000 when neither
        is given.
    resolution : float or tuple of float, optional
        Pixel spacing in target CRS units (e.g. degrees or metres).  A single
        value sets the same spacing in both directions; a 2-tuple sets
        ``(dx, dy)`` separately.  Mutually exclusive with ``nx``/``ny``.

    Examples
    --------
    >>> NearestNeighbour()  # 1000 × 1000 pixels
    >>> NearestNeighbour("auto")  # automatically sized to data and subplot
    >>> NearestNeighbour(nx=500, ny=500)  # fixed pixel count
    >>> NearestNeighbour(resolution=1.0)  # 1-degree pixels (PlateCarree)
    >>> NearestNeighbour(resolution=(1.0, 0.5))  # 1° × 0.5° pixels
    """


# Backwards-compatible alias
GridSample = Bilinear
