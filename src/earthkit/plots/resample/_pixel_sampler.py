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

    The output grid can be specified in two ways:

    - **Fixed pixel count** (``nx``/``ny``): always produces exactly that many
      pixels regardless of the map extent.
    - **Fixed resolution** (``resolution``): the pixel spacing is fixed in the
      target CRS units (degrees for PlateCarree, metres for projected CRS), so
      the pixel count adapts to the map extent.

    Use the :meth:`at_resolution` class method as a named constructor when
    specifying a resolution is more natural than a pixel count.

    Parameters
    ----------
    nx : int, optional
        Number of pixels in the x direction.  Mutually exclusive with
        ``resolution``.  Defaults to 1000 when neither is given.
    ny : int, optional
        Number of pixels in the y direction.  Mutually exclusive with
        ``resolution``.  Defaults to 1000 when neither is given.
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
                nx = ny = int(args[0])
            elif len(args) == 2:
                nx, ny = int(args[0]), int(args[1])
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
            self.nx = None
            self.ny = None
        else:
            self._dx = self._dy = None
            self._resolution_mode = False
            self.nx = nx if nx is not None else self.DEFAULT_NX
            self.ny = ny if ny is not None else self.DEFAULT_NY

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

    def resolve(self, bbox, crs=None):
        """
        Return the concrete ``(nx, ny)`` for the given bounding box.

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

    def apply(self, *args, **kwargs):
        raise NotImplementedError(
            f"{self.__class__.__name__} is a rendering hint; it is handled internally during plotting."
        )

    def _repr_size(self):
        if self._resolution_mode:
            if self._dx == self._dy:
                return f"resolution={self._dx}"
            return f"resolution=({self._dx}, {self._dy})"
        return f"nx={self.nx}, ny={self.ny}"

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
    nx : int, optional
        Number of pixels in the x direction.  Mutually exclusive with
        ``resolution``.  Defaults to 1000 when neither is given.
    ny : int, optional
        Number of pixels in the y direction.  Mutually exclusive with
        ``resolution``.  Defaults to 1000 when neither is given.
    resolution : float or tuple of float, optional
        Pixel spacing in target CRS units (e.g. degrees or metres).  A single
        value sets the same spacing in both directions; a 2-tuple sets
        ``(dx, dy)`` separately.  Mutually exclusive with ``nx``/``ny``.

    Examples
    --------
    >>> Bilinear()  # 1000 × 1000 pixels
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
    nx : int, optional
        Number of pixels in the x direction.  Mutually exclusive with
        ``resolution``.  Defaults to 1000 when neither is given.
    ny : int, optional
        Number of pixels in the y direction.  Mutually exclusive with
        ``resolution``.  Defaults to 1000 when neither is given.
    resolution : float or tuple of float, optional
        Pixel spacing in target CRS units (e.g. degrees or metres).  A single
        value sets the same spacing in both directions; a 2-tuple sets
        ``(dx, dy)`` separately.  Mutually exclusive with ``nx``/``ny``.

    Examples
    --------
    >>> NearestNeighbour()  # 1000 × 1000 pixels
    >>> NearestNeighbour(nx=500, ny=500)  # fixed pixel count
    >>> NearestNeighbour(resolution=1.0)  # 1-degree pixels (PlateCarree)
    >>> NearestNeighbour(resolution=(1.0, 0.5))  # 1° × 0.5° pixels
    """


# Backwards-compatible alias
GridSample = Bilinear
