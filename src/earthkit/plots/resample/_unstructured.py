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

import cartopy.crs as ccrs

from earthkit.plots.resample._base import Resample


class Unstructured(Resample):
    """
    Resample unstructured (scattered) data onto a structured grid using interpolation.

    This resampler is designed for data without a regular grid — for example,
    satellite level-2 swath data — and interpolates the scattered points onto a
    regular two-dimensional grid before plotting.

    The output grid can be specified in two ways:

    - **Fixed pixel count** (``nx``/``ny``): always produces exactly that many
      grid points regardless of the data extent.  A single positional argument
      sets ``nx = ny``; two positional arguments set ``nx`` and ``ny`` independently.
    - **Fixed resolution** (``resolution``): the grid spacing is fixed in the
      units of the target CRS (degrees for PlateCarree, metres for projected
      CRS), so the grid point count adapts to the data extent.  Use the
      :meth:`at_resolution` class method as a named constructor for this mode.

    Parameters
    ----------
    nx : int, optional
        Number of grid points in the x direction.  Mutually exclusive with
        ``resolution``.  If neither ``nx`` nor ``ny`` nor ``resolution`` is
        given, the resolution is estimated automatically from the data.
    ny : int, optional
        Number of grid points in the y direction.  Mutually exclusive with
        ``resolution``.
    resolution : float or tuple of float, optional
        Grid spacing in target CRS units.  A single value sets the same spacing
        in both directions; a 2-tuple sets ``(dx, dy)`` separately.  Mutually
        exclusive with ``nx``/``ny``.
    method : str, optional
        Interpolation method passed to :func:`scipy.interpolate.griddata`.
        One of ``'linear'`` (default), ``'nearest'``, or ``'cubic'``.
    distance_threshold : None, float, int, or str, optional
        Maximum distance from a source data point for an output grid cell to
        receive a value.  Cells further than this threshold are set to NaN.

        - ``None`` (default): no threshold applied; all output cells are filled.
        - numeric: distance in the units of the target CRS.
        - ``'auto'``: estimated automatically from the data density.
        - ``'N cells'``: N output grid cells (e.g. ``'2 cells'``).
    transform : bool, optional
        Whether to transform the source coordinates to the target CRS before
        interpolating.  Default is ``True``.

    Examples
    --------
    >>> Unstructured()  # auto-detect resolution
    >>> Unstructured(1000)  # 1000 × 1000 grid
    >>> Unstructured(1000, 500)  # 1000 × 500 grid
    >>> Unstructured(nx=1000, ny=500)
    >>> Unstructured(resolution=0.1)  # 0.1-degree grid spacing
    >>> Unstructured.at_resolution(0.25)
    >>> Unstructured(method="nearest", distance_threshold="auto")
    """

    def __init__(
        self,
        *args,
        nx=None,
        ny=None,
        resolution=None,
        method: str = "linear",
        distance_threshold=None,
        transform: bool = True,
    ):
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
                    f"{self.__class__.__name__} accepts at most 2 positional "
                    f"arguments (nx, ny); received {len(args)}."
                )

        if resolution is not None and (nx is not None or ny is not None):
            raise ValueError(
                f"{self.__class__.__name__}: 'resolution' is mutually exclusive "
                "with 'nx'/'ny'."
            )

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
            self.nx = nx
            self.ny = ny

        self.method = method
        self.distance_threshold = distance_threshold
        self.transform = transform

    @classmethod
    def at_resolution(cls, dx, dy=None, **kwargs):
        """
        Create an ``Unstructured`` resampler with a fixed grid spacing.

        Parameters
        ----------
        dx : float
            Grid spacing in the x direction, in target CRS units (degrees for
            PlateCarree).
        dy : float, optional
            Grid spacing in the y direction.  If omitted, ``dy = dx``.
        **kwargs
            Additional keyword arguments passed to :class:`Unstructured`
            (e.g. ``method``, ``distance_threshold``).

        Returns
        -------
        Unstructured

        Examples
        --------
        >>> Unstructured.at_resolution(0.25)  # 0.25° × 0.25°
        >>> Unstructured.at_resolution(0.5, 1.0)  # 0.5° × 1.0°
        >>> Unstructured.at_resolution(0.1, distance_threshold="auto")
        """
        if dy is None:
            dy = dx
        return cls(resolution=(float(dx), float(dy)), **kwargs)

    def _resolve_shape(self, x, y):
        """
        Return the concrete ``(nx, ny)`` for the output grid.

        If ``resolution`` was specified, derives the grid point count from the
        data extent.  Otherwise returns the stored ``nx``/``ny`` (or ``None``
        to let :func:`~earthkit.plots.resample.grids.interpolate_unstructured`
        auto-detect from the data).
        """
        if not self._resolution_mode:
            return self.nx, self.ny

        x_range = float(x.max() - x.min())
        y_range = float(y.max() - y.min())
        nx = max(2, round(x_range / self._dx) + 1)
        ny = max(2, round(y_range / self._dy) + 1)
        return nx, ny

    def apply(self, x, y, z, source_crs=None, target_crs=None):
        """
        Apply interpolation to resample data onto a new grid.

        Parameters
        ----------
        x : array-like
            Source x-coordinates.
        y : array-like
            Source y-coordinates.
        z : array-like
            Source values to be interpolated.
        source_crs : CRS, optional
            Coordinate reference system of the source data.
        target_crs : CRS, optional
            Coordinate reference system of the target grid.

        Returns
        -------
        tuple of array-like
            ``(grid_x, grid_y, grid_z)`` on the output structured grid.
        """
        import warnings

        import numpy as np

        from earthkit.plots.resample.grids import (
            interpolate_unstructured,
            is_structured,
        )

        if is_structured(x, y):
            warnings.warn(
                "Data appears to be on a regular structured grid. "
                "Unstructured is designed for scattered/unstructured data. "
                "Consider using resample=Bilinear() instead for better results.",
                UserWarning,
                stacklevel=4,
            )

        if self.transform:
            source_crs = source_crs or ccrs.PlateCarree()
            target_crs = target_crs or ccrs.PlateCarree()
            transformed_points = target_crs.transform_points(
                source_crs, x.flatten(), y.flatten()
            )
            target_x = transformed_points[..., 0].reshape(x.shape)
            target_y = transformed_points[..., 1].reshape(y.shape)
        else:
            target_x, target_y = x, y

        # Drop points where the CRS transformation produced non-finite coordinates
        # (e.g. points that project to infinity in a regional or polar projection).
        valid = np.isfinite(target_x) & np.isfinite(target_y)
        target_x = target_x[valid]
        target_y = target_y[valid]
        z = z.flatten()[valid]

        nx, ny = self._resolve_shape(target_x, target_y)

        return interpolate_unstructured(
            target_x,
            target_y,
            z,
            target_shape=(nx, ny) if nx is not None and ny is not None else None,
            target_resolution=(self._dx, self._dy) if self._resolution_mode else None,
            method=self.method,
            distance_threshold=self.distance_threshold,
        )

    def _repr_size(self):
        if self._resolution_mode:
            if self._dx == self._dy:
                return f"resolution={self._dx}"
            return f"resolution=({self._dx}, {self._dy})"
        if self.nx is not None or self.ny is not None:
            return f"nx={self.nx}, ny={self.ny}"
        return "auto"

    def __repr__(self):
        parts = [self._repr_size()]
        if self.method != "linear":
            parts.append(f"method={self.method!r}")
        if self.distance_threshold is not None:
            parts.append(f"distance_threshold={self.distance_threshold!r}")
        return f"{self.__class__.__name__}({', '.join(parts)})"
