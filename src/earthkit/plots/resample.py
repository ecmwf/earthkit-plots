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
import numpy as np

from earthkit.plots.geo import grids

# Sentinel for resample="auto": resolved at plot time based on the source gridspec.
_AUTO = "auto"


class Resample:
    def apply(self, data):
        """
        Apply the resampling technique to the data. This method should be overridden by subclasses.

        Parameters
        ----------
        data : np.array
            The data to be resampled.

        Returns
        -------
        np.array
            The resampled data.

        Raises
        ------
        NotImplementedError
            If the subclass does not override this method.
        """
        raise NotImplementedError("Subclasses must override this method.")

    def __repr__(self):
        """
        Return a string representation of the resampler.

        Returns
        -------
        str
            A string that represents the resampler object. Can be customized by subclasses.
        """
        return f"{self.__class__.__name__}()"


class Subsample(Resample):
    def __init__(self, *args, nx=None, ny=None, mode="fixed"):
        if args:
            if any((nx, ny)):
                raise ValueError(
                    f"{self.__class__.__name__} can take positional arguments or "
                    "keyword arguments, but not a combination of both."
                )
            if len(args) == 1:
                self.nx = self.ny = args[0]
            elif len(args) == 2:
                self.nx, self.ny = args
            else:
                raise ValueError(
                    f"{self.__class__.__name__} can take at most 2 positional "
                    f"arguments; received {len(args)}"
                )
        else:
            self.nx = nx
            self.ny = ny

        self.shape = (self.nx, self.ny)

        if mode not in ["stride", "fixed"]:
            raise ValueError("Mode must be 'stride' or 'fixed'")
        self.mode = mode

    def _fixed_steps(self, x_values, y_values):
        x_step = 1
        if self.nx:
            if len(x_values.shape) == 1:
                x_step = len(x_values) // (self.nx - 1)
            else:
                x_step = x_values.shape[1] // (self.nx - 1)
            x_step = max(1, x_step)

        y_step = 1
        if self.ny:
            if len(y_values.shape) == 1:
                y_step = len(y_values) // (self.ny - 1)
            else:
                y_step = y_values.shape[0] // (self.ny - 1)
            y_step = max(1, y_step)

        return x_step, y_step

    def apply(self, x_values, y_values, *values, **kwargs):
        if self.mode == "stride":
            x_step = self.nx
            y_step = self.ny
        elif self.mode == "fixed":
            x_step, y_step = self._fixed_steps(x_values, y_values)

        if len(x_values.shape) == 1:
            x_values = x_values[::x_step]
        else:
            x_values = x_values[::y_step, ::x_step]

        if len(y_values.shape) == 1:
            y_values = y_values[::y_values]
        else:
            y_values = y_values[::y_step, ::x_step]

        values = (v[::y_step, ::x_step] for v in values)

        return [x_values, y_values, *values]

    def __repr__(self):
        return f"{self.__class__.__name__}(nx={self.nx}, ny={self.ny})"


def _convert_spec(spec):
    """Normalise a grid spec to a plain dict for earthkit-regrid."""
    if not isinstance(spec, dict):
        if hasattr(spec, "spec"):
            return spec.spec
        elif hasattr(spec, "to_dict"):
            return spec.to_dict()
        raise ValueError(
            "Grid spec must be a dict or have a 'spec' property or a 'to_dict' method."
        )
    return spec


def _is_structured_grid(gridspec):
    """
    Return True when *gridspec* indicates a HEALPix or reduced Gaussian grid —
    the only grids for which earthkit-regrid is used.

    Gridspec objects (``GridSpec``, ``LegacyGridSpec``) carry a ``.name``
    property that returns ``'healpix'``, ``'reduced_gg'``, or ``'unknown'``.
    Plain dicts (e.g. from a user-supplied ``source_grid``) are inspected for a
    ``"grid"`` key whose value matches the HEALPix (``H<N>``) or reduced
    Gaussian (``O<N>`` / ``N<N>``) naming conventions.
    """
    if gridspec is None:
        return False

    # Prefer the .name property on GridSpec / LegacyGridSpec objects
    if hasattr(gridspec, "name"):
        return gridspec.name in ("healpix", "reduced_gg")

    # Fall back to inspecting the dict representation
    if isinstance(gridspec, dict):
        grid_value = gridspec.get("grid", "")
    else:
        try:
            d = _convert_spec(gridspec)
            grid_value = d.get("grid", "") if isinstance(d, dict) else ""
        except Exception:
            return False

    if not isinstance(grid_value, str):
        return False

    import re

    grid_lower = grid_value.lower()
    # H<N> = HEALPix,  O<N> or N<N> = reduced Gaussian
    return bool(re.match(r"^h\d+", grid_lower) or re.match(r"^[on]\d+", grid_lower))


class _LegacyRegridExecutor:
    subarea_support = False

    @staticmethod
    def is_valid():
        try:
            from earthkit.regrid import interpolate  # noqa: F401

            return True
        except ImportError:
            return False

    @staticmethod
    def call(array, in_grid, out_grid):
        from earthkit.regrid import interpolate

        return interpolate(array, in_grid=in_grid, out_grid=out_grid)


class _MirRegridExecutor:
    subarea_support = True

    @staticmethod
    def is_valid():
        try:
            from earthkit.regrid.array import regrid  # noqa: F401

            try:
                import mir  # noqa: F401
            except Exception:
                return False
            return True
        except ImportError:
            return False

    @staticmethod
    def call(array, in_grid, out_grid):
        import logging

        from earthkit.regrid.array import regrid

        LOG = logging.getLogger(__name__)
        _kwargs = {}
        if isinstance(in_grid, dict) and "icon" in in_grid.get("grid", "").lower():
            _kwargs["interpolation"] = "nn"
        LOG.debug("Regridding using MIR, in_grid=%s out_grid=%s", in_grid, out_grid)
        r = regrid(array, in_grid=in_grid, out_grid=out_grid, **_kwargs)
        return r[0]


_REGRID_METHOD_ALIASES = {
    "nearest": "nearest-neighbour",
}

_VALID_REGRID_METHODS = {"linear", "nearest-neighbour"}


class Regrid(Resample):
    """
    Resample data onto a regular latitude/longitude grid using earthkit-regrid.

    This resampler converts the source data to a regular lat/lon grid **in data
    space** before plotting, making the result independent of the target map
    CRS.  Regridding via earthkit-regrid is only attempted when the source data
    is on a HEALPix or reduced Gaussian grid (detected either from the source's
    own gridspec or from the explicit ``source_grid`` argument).  For all other
    grids the class raises an informative error — use :class:`Bilinear` or
    :class:`NearestNeighbour` for generic lat/lon data instead.

    Parameters
    ----------
    resolution : float, optional
        Output grid spacing in degrees.  Defaults to ``0.25``.
    method : str, optional
        Interpolation method: ``'linear'`` (default) or ``'nearest-neighbour'``
        (alias ``'nearest'``).
    source_grid : dict, optional
        Explicit earthkit-regrid input grid spec.  If provided it overrides
        whatever gridspec the source carries.  Use this when the source does not
        carry metadata (e.g. raw numpy arrays) but the grid type is known.

    Examples
    --------
    >>> Regrid()  # 0.25° lat/lon, linear
    >>> Regrid(resolution=1.0)  # 1° lat/lon
    >>> Regrid(resolution=0.5, method="nearest")
    >>> Regrid(source_grid={"grid": "healpix", "ordering": "ring", "nside": 32})
    >>> Regrid.at_resolution(0.1)
    """

    DEFAULT_RESOLUTION = 0.25

    def __init__(self, resolution=None, method="linear", source_grid=None):
        self._resolution = (
            float(resolution) if resolution is not None else self.DEFAULT_RESOLUTION
        )

        method = _REGRID_METHOD_ALIASES.get(method, method)
        if method not in _VALID_REGRID_METHODS:
            raise ValueError(
                f"Regrid: method must be one of {sorted(_VALID_REGRID_METHODS)!r}, "
                f"got {method!r}."
            )
        self.method = method
        self.source_grid = source_grid

    @classmethod
    def at_resolution(cls, resolution, method="linear", source_grid=None):
        """
        Create a :class:`Regrid` resampler at a specific output resolution.

        Parameters
        ----------
        resolution : float
            Output grid spacing in degrees.
        method : str, optional
            Interpolation method (``'linear'`` or ``'nearest-neighbour'``).
        source_grid : dict, optional
            Explicit input grid spec for earthkit-regrid.

        Returns
        -------
        Regrid
        """
        return cls(resolution=resolution, method=method, source_grid=source_grid)

    # ------------------------------------------------------------------
    # earthkit-regrid availability helpers (replaces geo/regrid.py)
    # ------------------------------------------------------------------

    @staticmethod
    def _find_executor():
        """Return the best available regrid executor, or None."""
        for cls in [_MirRegridExecutor, _LegacyRegridExecutor]:
            if cls.is_valid():
                return cls
        return None

    @classmethod
    def available(cls):
        """Return True if earthkit-regrid is installed and usable."""
        return cls._find_executor() is not None

    @classmethod
    def has_subarea_support(cls):
        """Return True if the available executor supports sub-area regridding."""
        executor = cls._find_executor()
        return executor.subarea_support if executor is not None else False

    @staticmethod
    def _call_regrid(array, in_grid, out_grid):
        """Call the best available executor."""
        executor = Regrid._find_executor()
        if executor is None:
            raise ImportError(
                "Regridding not available. Please install the earthkit-regrid package."
            )
        return executor.call(array, in_grid, out_grid)

    # ------------------------------------------------------------------
    # Public apply
    # ------------------------------------------------------------------

    def apply(self, x_values, y_values, z_values, gridspec=None, context=None):
        """
        Regrid ``z_values`` onto a regular lat/lon grid via earthkit-regrid.

        Parameters
        ----------
        x_values, y_values : np.ndarray
            Source coordinate arrays (passed through unchanged; the regridder
            uses the gridspec, not the coordinate arrays).
        z_values : np.ndarray
            Source data values.
        gridspec : optional
            Grid specification from the source object.  Merged with
            ``self.source_grid`` (the explicit arg takes precedence).
        context : PlotContext, optional
            Only geographic plots are regridded; Cartesian plots are
            returned unchanged.

        Returns
        -------
        tuple[np.ndarray, np.ndarray, np.ndarray]
            ``(lon_2d, lat_2d, z_2d)`` on the regular lat/lon output grid.
        """
        from earthkit.plots.sources.context import PlotContext

        _context = context or PlotContext.GEOGRAPHIC_2D
        if not _context.is_geographic:
            return x_values, y_values, z_values

        # Determine the effective in_grid spec
        in_grid = self.source_grid or gridspec
        if in_grid is None or not _is_structured_grid(in_grid):
            raise ValueError(
                "Regrid can only be used with HEALPix or reduced Gaussian source grids. "
                "Pass source_grid=<gridspec> explicitly, or use Bilinear/NearestNeighbour "
                "for regular lat/lon data."
            )

        in_grid_spec = _convert_spec(in_grid)
        out_grid_spec = {"grid": [self._resolution, self._resolution]}
        if self.method == "nearest-neighbour":
            out_grid_spec["interpolation"] = "nearest-neighbour"

        z_new = self._call_regrid(
            z_values, in_grid=in_grid_spec, out_grid=out_grid_spec
        )
        lon_2d, lat_2d = _generate_latlon_grid(self._resolution)
        return lon_2d, lat_2d, z_new

    def __repr__(self):
        parts = [f"resolution={self._resolution}", f"method={self.method!r}"]
        if self.source_grid is not None:
            parts.append(f"source_grid={self.source_grid!r}")
        return f"{self.__class__.__name__}({', '.join(parts)})"


class Chain(Resample):
    """
    Apply two or more resample steps in sequence.

    Pass a list (or multiple positional arguments) of :class:`Resample`
    instances.  Steps are applied in order: data-space resamplers first
    (e.g. :class:`Regrid`), pixel-space resamplers last (e.g.
    :class:`Bilinear`, :class:`NearestNeighbour`).

    Examples
    --------
    >>> Chain(Regrid(5), Bilinear())  # regrid to 5° then pixel-sample
    >>> Chain([Regrid(), Bilinear()])  # same via list
    """

    def __init__(self, *steps):
        if len(steps) == 1 and isinstance(steps[0], (list, tuple)):
            steps = steps[0]
        if len(steps) < 2:
            raise ValueError("Chain requires at least two resample steps.")
        self.steps = list(steps)

    @property
    def data_steps(self):
        """Non-pixel-sampler steps, applied in data space (Step 6.5)."""
        return [s for s in self.steps if not isinstance(s, _PixelSampler)]

    @property
    def pixel_step(self):
        """The last _PixelSampler step, or None (applied at Step 8.5)."""
        pixel_steps = [s for s in self.steps if isinstance(s, _PixelSampler)]
        return pixel_steps[-1] if pixel_steps else None

    def __repr__(self):
        return f"Chain({', '.join(repr(s) for s in self.steps)})"


def _generate_latlon_grid(resolution):
    """Generate a 2-D regular lat/lon meshgrid at *resolution* degrees."""
    lat_v = np.linspace(90, -90, int(180 / resolution) + 1)
    lon_v = np.linspace(0, 360 - resolution, int(360 / resolution))
    lon, lat = np.meshgrid(lon_v, lat_v)
    return lon, lat


def _call_regrid_compat(array, in_grid, out_grid):
    """
    Module-level helper that exposes the regrid call for the geo/regrid shim.
    """
    in_grid = _convert_spec(in_grid)
    out_grid = _convert_spec(out_grid)
    return Regrid._call_regrid(array, in_grid=in_grid, out_grid=out_grid)


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
            self.nx = nx if nx is not None else self.DEFAULT_NX
            self.ny = ny if ny is not None else self.DEFAULT_NY

    @classmethod
    def at_resolution(cls, dx, dy=None):
        """
        Create a sampler with a fixed pixel spacing in the target CRS units.

        This is the preferred named constructor when you want to specify a
        resolution (e.g. 1 degree or 5000 metres) rather than an absolute
        pixel count.  The actual number of pixels adapts to the map extent at
        render time.

        Parameters
        ----------
        dx : float
            Pixel spacing in the x direction, in target CRS units (e.g.
            degrees for PlateCarree, metres for a projected CRS).
        dy : float, optional
            Pixel spacing in the y direction.  If omitted, ``dy = dx``
            (square pixels).

        Returns
        -------
        _PixelSampler subclass instance

        Examples
        --------
        >>> Bilinear.at_resolution(1.0)  # 1° × 1° pixels
        >>> NearestNeighbour.at_resolution(0.25)  # quarter-degree pixels
        >>> Bilinear.at_resolution(5000, 5000)  # 5 km × 5 km pixels (projected)
        """
        if dy is None:
            dy = dx
        return cls(resolution=(float(dx), float(dy)))

    def resolve(self, bbox):
        """
        Return the concrete ``(nx, ny)`` for the given bounding box.

        Parameters
        ----------
        bbox : tuple
            ``(xmin, xmax, ymin, ymax)`` in the target CRS units.

        Returns
        -------
        nx, ny : int
        """
        if not self._resolution_mode:
            return self.nx, self.ny
        xmin, xmax, ymin, ymax = bbox
        nx = max(1, round(abs(xmax - xmin) / self._dx))
        ny = max(1, round(abs(ymax - ymin) / self._dy))
        return nx, ny

    def apply(self, *args, **kwargs):
        raise NotImplementedError(
            f"{self.__class__.__name__} is a rendering hint; "
            "it is handled internally during plotting."
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


class Interpolate(Resample):
    """
    Resample data onto a new grid using interpolation.

    Parameters
    ----------
    target_shape : None | tuple[int, int] | int, optional
        The shape of the target grid. If an integer is provided, the target grid will be square.
    target_resolution : None | tuple[float, float] | float, optional
        The resolution of the target grid. If a float is provided, the target grid will be square.
    method : str, optional
        The interpolation method to use. Must be one of 'linear', 'nearest', or 'cubic'.
    distance_threshold : None | float | int | str, optional
        The maximum distance between the source and target points for interpolation to be used.
        If None, all points will be used.
    transform : bool, optional
        Whether to transform the source coordinates to the target CRS before resampling.
        Default is True.
    """

    def __init__(
        self,
        target_shape: None | tuple[int, int] | int = None,
        target_resolution: None | tuple[float, float] | float = None,
        method: str = "linear",
        distance_threshold: None | float | int | str = None,
        transform: bool = True,
    ):
        """
        Initialize the interpolation resampler.
        """
        if target_shape is not None and not isinstance(target_shape, (tuple, list)):
            target_shape = (target_shape, target_shape)

        if target_resolution is not None and not isinstance(
            target_resolution, (tuple, list)
        ):
            target_resolution = (target_resolution, target_resolution)

        self.target_shape = target_shape
        self.target_resolution = target_resolution
        self.method = method
        self.distance_threshold = distance_threshold
        self.transform = transform

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
        array-like
            Interpolated values on the target grid.
        """
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

        return grids.interpolate_unstructured(
            target_x,
            target_y,
            z,
            target_shape=self.target_shape,
            target_resolution=self.target_resolution,
            method=self.method,
            distance_threshold=self.distance_threshold,
        )

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(target_shape={self.target_shape}, "
            f"target_resolution={self.target_resolution}, method={self.method}, "
            f"distance_threshold={self.distance_threshold})"
        )
