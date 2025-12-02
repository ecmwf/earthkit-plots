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
import matplotlib.pyplot as plt

from earthkit.plots.core.maps import Map
from earthkit.plots.geo.coordinate_reference_systems import is_cylindrical


class Tile(Map):
    """
    A specialized Map for creating WMS tiles with exact pixel dimensions.

    This class creates map tiles that:
    - Accept dimensions in pixels (e.g., size=(512, 512))
    - Respect dimensions perfectly when saving
    - Have no padding or border around edges
    - Fill out-of-bounds areas with transparency

    Parameters
    ----------
    domain : str, tuple, list or Domain, optional
        The domain of the tile. Can be a string, a tuple or a list of
        coordinates, or a :class:`earthkit.plots.geo.domains.Domain` object.
    size : tuple of int, optional
        The size of the tile in pixels, e.g., (512, 512). Default is (256, 256).
    crs : cartopy.crs.CRS, optional
        The CRS of the tile. If not provided, it will be inferred from the
        domain.
    dpi : int, optional
        The DPI to use for rendering. Higher DPI values produce better quality
        but take longer to render. For high-quality tiles, use 200-300.
        Default is 100.
    rasterization_dpi : int, optional
        The DPI to use for rasterizing vector elements (coastlines, etc.).
        If not specified, defaults to max(dpi * 2, 200) for better quality.
    **kwargs
        Additional keyword arguments to pass to the :class:`Map` constructor.

    Examples
    --------
    >>> tile = Tile(domain=[-10, 50, 35, 70], size=(512, 512))
    >>> tile.coastlines()
    >>> tile.save("tile.png")
    """

    def __init__(self, domain=None, size=(256, 256), crs=None, dpi=100, rasterization_dpi=None, **kwargs):
        self._pixel_size = size
        self._dpi = dpi

        # If rasterization_dpi not specified, use a higher value for better quality
        # This controls the resolution of rasterized elements (coastlines, etc.)
        if rasterization_dpi is None:
            # Use at least 2x the output DPI for better quality, or 200 minimum
            rasterization_dpi = max(dpi * 2, 200)
        self._rasterization_dpi = rasterization_dpi

        # Convert pixel size to inches based on DPI
        figsize = (size[0] / dpi, size[1] / dpi)

        # Create a standalone figure for this tile
        self._fig = plt.figure(figsize=figsize, dpi=dpi)
        self._fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        self._fig.patch.set_alpha(0)

        # Create gridspec
        self._gridspec = self._fig.add_gridspec(1, 1)

        # Create a minimal figure wrapper for Map
        figure = _TileFigure(self._fig, self._gridspec)

        # Initialize parent Map
        super().__init__(row=0, column=0, figure=figure, domain=domain, crs=crs, **kwargs)

        # Flag to track if we're using matplotlib-only rendering for cylindrical projections
        self._use_matplotlib_only = False

    def _ensure_axes(self):
        """Override to add tile-specific axes configuration and handle cylindrical projections."""
        if self._ax is not None:
            return  # Axes already exist

        # Check if we should use matplotlib-only rendering for cylindrical projections
        # This allows multi-wrap support (e.g., domains like [-380, 240, -90, 90])
        if self._crs is not None and is_cylindrical(self._crs):
            self._use_matplotlib_only = True
            self._create_matplotlib_axes()
        else:
            # Use normal cartopy-based rendering
            super()._ensure_axes()

            # Add tile-specific configuration
            if self._ax is not None:
                # Make axes background transparent
                self._ax.patch.set_alpha(0)

                # Handle out-of-bounds domains BEFORE setting aspect
                # This ensures proper positioning
                if self.domain is not None:
                    self._handle_out_of_bounds_domain()

                # Set aspect to auto to allow stretching/compressing to fill exact dimensions
                # Do this AFTER handling out-of-bounds to ensure it applies correctly
                self._ax.set_aspect('auto')

    def _create_matplotlib_axes(self):
        """
        Create plain matplotlib axes for cylindrical projection rendering.

        This bypasses cartopy's GeoAxes to enable multi-wrap support.
        """
        # Create plain matplotlib axes
        self._ax = self._fig.add_subplot(
            self._gridspec[0, 0],
            **self._ax_kwargs,
        )

        # Make axes background transparent
        self._ax.patch.set_alpha(0)

        # Set domain extent if specified
        if self.domain is not None and None not in list(self.domain.bbox):
            bounds = self.domain.bbox.to_cartopy_bounds()
            # For matplotlib axes, just set xlim and ylim
            # Transform coordinates if needed (e.g., for Web Mercator)
            x_min, x_max, y_min, y_max = self._transform_bounds_to_display(bounds)
            self._ax.set_xlim(x_min, x_max)
            self._ax.set_ylim(y_min, y_max)

            # Calculate and apply proper aspect ratio for the projection
            # This ensures the map maintains correct proportions with transparent areas as needed
            data_aspect = self._calculate_aspect_ratio(x_min, x_max, y_min, y_max)

            # Calculate axes position to preserve aspect ratio within tile
            tile_width, tile_height = self._pixel_size
            tile_aspect = tile_width / tile_height

            if data_aspect > tile_aspect:
                # Data is wider than tile - fit width, add transparency top/bottom
                axes_height = tile_aspect / data_aspect
                axes_bottom = (1 - axes_height) / 2
                self._ax.set_position([0, axes_bottom, 1, axes_height])
            else:
                # Data is taller than tile - fit height, add transparency left/right
                axes_width = data_aspect / tile_aspect
                axes_left = (1 - axes_width) / 2
                self._ax.set_position([axes_left, 0, axes_width, 1])

            # Set aspect to equal to maintain proper proportions
            self._ax.set_aspect('equal', adjustable='box')
        else:
            # No domain specified, use auto aspect
            self._ax.set_aspect('auto')

        # Hide axes decorations
        self._ax.axis('off')

        # Replay queued method calls
        self._replay_method_queue()

    def _transform_bounds_to_display(self, bounds):
        """
        Transform domain bounds to display coordinates for the CRS.

        For PlateCarree (EPSG:4326), this is a no-op.
        For Mercator (EPSG:3857), this transforms lat/lon to meters.

        Parameters
        ----------
        bounds : tuple
            (x_min, x_max, y_min, y_max) in the domain's CRS

        Returns
        -------
        tuple
            (x_min, x_max, y_min, y_max) in display coordinates
        """
        x_min, x_max, y_min, y_max = bounds

        # Use cartopy to transform if needed
        if self._crs is not None:
            import cartopy.crs as ccrs
            # Get the domain's CRS (usually PlateCarree for lat/lon)
            domain_crs = self.domain.bbox.crs if hasattr(self.domain.bbox, 'crs') else ccrs.PlateCarree()

            # Check if CRSs are the same type - if so, no transformation needed
            if type(self._crs).__name__ == type(domain_crs).__name__:
                return bounds

            # Transform the four corners to get proper bounds
            # We need to transform all four corners and then take min/max
            x_coords = np.array([x_min, x_max, x_min, x_max])
            y_coords = np.array([y_min, y_min, y_max, y_max])

            transformed = self._crs.transform_points(domain_crs, x_coords, y_coords)

            # Extract x and y from transformed points and get bounds
            x_transformed = transformed[:, 0]
            y_transformed = transformed[:, 1]

            return (x_transformed.min(), x_transformed.max(),
                    y_transformed.min(), y_transformed.max())

        return bounds

    def _calculate_aspect_ratio(self, x_min, x_max, y_min, y_max):
        """
        Calculate the proper aspect ratio for the projection.

        This calculates the aspect ratio based on the display coordinates
        (already transformed to the target CRS). For cylindrical projections,
        this gives us the correct aspect ratio to maintain proper map proportions.

        Parameters
        ----------
        x_min, x_max, y_min, y_max : float
            Bounds in display coordinates (after CRS transformation)

        Returns
        -------
        float
            The aspect ratio (width / height) in display coordinates
        """
        x_extent = x_max - x_min
        y_extent = y_max - y_min

        if y_extent == 0:
            return 1.0

        # For cylindrical projections, the aspect ratio is simply
        # the ratio of x extent to y extent in display coordinates
        return x_extent / y_extent

    def _transform_coordinates(self, x, y, source_crs=None):
        """
        Transform data coordinates to display coordinates for the CRS.

        Parameters
        ----------
        x, y : array-like
            Coordinate arrays in source CRS
        source_crs : cartopy.crs.CRS, optional
            Source CRS. If None, assumes PlateCarree.

        Returns
        -------
        tuple
            (x_display, y_display) in display coordinates
        """
        if not self._use_matplotlib_only:
            # Not using matplotlib-only mode, return as-is
            return x, y

        import cartopy.crs as ccrs
        if source_crs is None:
            source_crs = ccrs.PlateCarree()

        # Transform using cartopy
        x_flat = np.asarray(x).ravel()
        y_flat = np.asarray(y).ravel()

        transformed = self._crs.transform_points(source_crs, x_flat, y_flat)
        x_transformed = transformed[:, 0].reshape(np.asarray(x).shape)
        y_transformed = transformed[:, 1].reshape(np.asarray(y).shape)

        return x_transformed, y_transformed

    def _tile_data_for_multiwrap(self, x, y, z):
        """
        Tile data to cover multi-wrap longitude domains.

        For domains that extend beyond 360° in longitude, this repeats
        the data as many times as needed to fill the domain.

        Parameters
        ----------
        x, y, z : array-like
            Coordinate and data arrays

        Returns
        -------
        tuple
            (x_tiled, y_tiled, z_tiled) with data repeated to cover domain
        """
        if not self._use_matplotlib_only or self.domain is None:
            return x, y, z

        # Get domain bounds
        bounds = self.domain.bbox.to_cartopy_bounds()
        lon_min, lon_max = bounds[0], bounds[1]
        lon_extent = lon_max - lon_min

        # Check if we need multi-wrap (extent >= 360°)
        if lon_extent < 360:
            return x, y, z

        # Check if data looks global (covers most/all of 360°)
        x_arr = np.asarray(x)
        x_min = float(x_arr.min())
        x_max = float(x_arr.max())
        x_span = x_max - x_min

        # Data should span at least 300° to be considered wrappable
        if x_span < 300:
            return x, y, z

        # Calculate which 360° tiles we need to cover the domain
        num_complete_wraps = int(np.ceil(lon_extent / 360))

        # Generate offsets that will cover the domain
        start_offset = int(np.floor(lon_min / 360)) * 360

        offsets = []
        for i in range(num_complete_wraps + 1):  # +1 to ensure full coverage
            offset = start_offset + (i * 360)
            # Check if this offset would place data within the domain
            offset_x_min = x_min + offset
            offset_x_max = x_max + offset

            # Include this tile if it overlaps with the domain
            if offset_x_max >= lon_min and offset_x_min <= lon_max:
                offsets.append(offset)

        if len(offsets) < 1:
            return x, y, z

        # Tile the data
        if x_arr.ndim == 1:
            # 1D coordinates
            x_tiles = [x_arr + offset for offset in offsets]
            x_tiled = np.concatenate(x_tiles)

            # Tile z horizontally
            z_tiled = np.tile(z, (1, len(offsets)))

            # y stays the same or tiles if 2D
            y_arr = np.asarray(y)
            if y_arr.ndim == 2:
                y_tiled = np.tile(y_arr, (1, len(offsets)))
            else:
                y_tiled = y_arr

        elif x_arr.ndim == 2:
            # 2D coordinates (meshgrid)
            x_tiles = [x_arr + offset for offset in offsets]
            x_tiled = np.concatenate(x_tiles, axis=1)

            y_arr = np.asarray(y)
            y_tiled = np.tile(y_arr, (1, len(offsets)))
            z_tiled = np.tile(z, (1, len(offsets)))
        else:
            return x, y, z

        return x_tiled, y_tiled, z_tiled

    def _plot_kwargs(self, *args, **kwargs):
        """
        Override to signal matplotlib-only rendering mode to extractors.

        When using matplotlib-only mode (for cylindrical projections with multi-wrap),
        we signal this to extractors so they don't set the cartopy 'transform' kwarg.
        """
        kwargs = super()._plot_kwargs(*args, **kwargs)

        # Signal to extractors that we're in matplotlib-only mode
        if self._use_matplotlib_only:
            kwargs['_tile_matplotlib_only'] = True

        return kwargs

    @property
    def ax(self):
        """Override to wrap axes with coordinate transformation support."""
        self._ensure_axes()

        # If using matplotlib-only mode, wrap the axes to intercept plotting calls
        if self._use_matplotlib_only and not hasattr(self._ax, '_tile_wrapped'):
            self._ax = _TileAxesWrapper(self._ax, self._crs)
            self._ax._tile_wrapped = True

        return self._ax

    def _handle_out_of_bounds_domain(self):
        """
        Clip the domain to valid CRS bounds and adjust axes positioning.

        For domains that extend beyond valid CRS bounds (e.g., lat > 90),
        this clips to valid bounds and positions the map correctly within
        the tile, leaving out-of-bounds areas transparent.
        """
        import cartopy.crs as ccrs

        # Get the requested domain bounds
        domain_bounds = self.domain.bbox.to_cartopy_bounds()
        x_min, x_max, y_min, y_max = domain_bounds

        # Get valid CRS bounds
        # For PlateCarree and similar, latitude is limited to [-90, 90]
        crs_name = self.crs.__class__.__name__

        if crs_name == 'PlateCarree' or crs_name == 'Geodetic':
            # Clip to valid latitude range
            valid_y_min = max(y_min, -90)
            valid_y_max = min(y_max, 90)
            valid_x_min = x_min
            valid_x_max = x_max
        else:
            # For other projections, try to get their bounds
            # If not available, use the domain as-is
            try:
                crs_bounds = self.crs.x_limits + self.crs.y_limits
                valid_x_min = max(x_min, crs_bounds[0])
                valid_x_max = min(x_max, crs_bounds[1])
                valid_y_min = max(y_min, crs_bounds[2])
                valid_y_max = min(y_max, crs_bounds[3])
            except (AttributeError, TypeError):
                # CRS doesn't have limits, use domain as-is
                return

        # If bounds were clipped, we need to adjust the axes position
        # to maintain the correct pixel dimensions
        if (valid_y_min != y_min or valid_y_max != y_max or
            valid_x_min != x_min or valid_x_max != x_max):

            # Set extent to valid bounds only
            self._ax.set_extent(
                [valid_x_min, valid_x_max, valid_y_min, valid_y_max],
                self.domain.bbox.crs
            )

            # Calculate the fraction of the tile that the valid area occupies
            # This ensures the valid map area is positioned correctly
            total_y_range = y_max - y_min
            total_x_range = x_max - x_min

            if total_y_range > 0 and total_x_range > 0:
                # Calculate position of valid area within the requested domain
                # Note: In figure coordinates, (0,0) is bottom-left, (1,1) is top-right
                y_start_frac = (valid_y_min - y_min) / total_y_range
                y_end_frac = (valid_y_max - y_min) / total_y_range
                x_start_frac = (valid_x_min - x_min) / total_x_range
                x_end_frac = (valid_x_max - x_min) / total_x_range

                # Set axes position directly in figure coordinates
                # Since we set subplots_adjust(0, 1, 0, 1), the axes should fill the figure
                # We adjust to position the valid area correctly
                self._ax.set_position([x_start_frac, y_start_frac,
                                      x_end_frac - x_start_frac,
                                      y_end_frac - y_start_frac])

    def save(self, filename, **kwargs):
        """
        Save the tile to a file with exact pixel dimensions.

        Parameters
        ----------
        filename : str or file-like object
            The file to which to save the tile.
        **kwargs
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.savefig`.
            Note: 'bbox_inches', 'pad_inches', and 'dpi' will be overridden to ensure
            exact pixel dimensions.

        Returns
        -------
        None
        """
        # Override settings to ensure exact pixel dimensions
        kwargs['bbox_inches'] = None
        kwargs['pad_inches'] = 0
        kwargs['dpi'] = self._dpi
        kwargs['transparent'] = kwargs.get('transparent', True)

        # Enable figure-level antialiasing for smoother rendering
        # This is the default but we make it explicit
        if 'facecolor' not in kwargs:
            kwargs['facecolor'] = 'none'  # Transparent background
        if 'edgecolor' not in kwargs:
            kwargs['edgecolor'] = 'none'

        # Set rasterization DPI for better quality of vector elements
        # This affects how cartopy features (coastlines, etc.) are rasterized
        if 'metadata' not in kwargs:
            kwargs['metadata'] = {}

        self.ax.axis('off')

        # Use the figure's savefig directly instead of plt.savefig
        self._fig.savefig(filename, **kwargs)

    def show(self):
        """
        Display the tile.

        This calls :func:`matplotlib.pyplot.show` to display the tile.
        """
        plt.show()


class _TileAxesWrapper:
    """
    Wrapper for matplotlib axes that handles coordinate transformation for Tile.

    This intercepts plotting calls to transform coordinates from source CRS
    (e.g., lat/lon) to display CRS (e.g., Web Mercator meters) when rendering
    with plain matplotlib instead of cartopy.
    """

    def __init__(self, ax, target_crs):
        self._ax = ax
        self._target_crs = target_crs

    def __getattr__(self, name):
        """Delegate all other attributes to the wrapped axes."""
        return getattr(self._ax, name)

    def _transform_coords(self, x, y, source_crs):
        """Transform coordinates from source CRS to target CRS."""
        if source_crs is None or source_crs == self._target_crs:
            return x, y

        # Use cartopy to transform coordinates
        x_arr = np.asarray(x)
        y_arr = np.asarray(y)

        # Handle both 1D and 2D coordinate arrays
        original_shape_x = x_arr.shape
        original_shape_y = y_arr.shape

        x_flat = x_arr.ravel()
        y_flat = y_arr.ravel()

        transformed = self._target_crs.transform_points(source_crs, x_flat, y_flat)
        x_transformed = transformed[:, 0].reshape(original_shape_x)
        y_transformed = transformed[:, 1].reshape(original_shape_y)

        return x_transformed, y_transformed

    def _remove_cartopy_kwargs(self, kwargs):
        """Remove any cartopy-specific kwargs that would break matplotlib."""
        # Remove transform kwarg completely (cartopy-specific)
        kwargs.pop('transform', None)
        kwargs.pop('transform_first', None)
        # Remove our internal marker
        source_crs = kwargs.pop('_source_crs', None)
        return source_crs

    def contour(self, *args, **kwargs):
        """Intercept contour to transform coordinates."""
        source_crs = self._remove_cartopy_kwargs(kwargs)
        if source_crs and len(args) >= 3:
            x_transformed, y_transformed = self._transform_coords(args[0], args[1], source_crs)
            args = (x_transformed, y_transformed) + args[2:]
        return self._ax.contour(*args, **kwargs)

    def contourf(self, *args, **kwargs):
        """Intercept contourf to transform coordinates."""
        source_crs = self._remove_cartopy_kwargs(kwargs)
        if source_crs and len(args) >= 3:
            x_transformed, y_transformed = self._transform_coords(args[0], args[1], source_crs)
            args = (x_transformed, y_transformed) + args[2:]
        return self._ax.contourf(*args, **kwargs)

    def pcolormesh(self, *args, **kwargs):
        """Intercept pcolormesh to transform coordinates."""
        source_crs = self._remove_cartopy_kwargs(kwargs)
        if source_crs and len(args) >= 3:
            x_transformed, y_transformed = self._transform_coords(args[0], args[1], source_crs)
            args = (x_transformed, y_transformed) + args[2:]
        return self._ax.pcolormesh(*args, **kwargs)

    def imshow(self, *args, **kwargs):
        """Intercept imshow - no coordinate transformation needed (already in pixel space)."""
        self._remove_cartopy_kwargs(kwargs)
        return self._ax.imshow(*args, **kwargs)

    def scatter(self, *args, **kwargs):
        """Intercept scatter to transform coordinates."""
        source_crs = self._remove_cartopy_kwargs(kwargs)
        if source_crs and len(args) >= 2:
            x_transformed, y_transformed = self._transform_coords(args[0], args[1], source_crs)
            args = (x_transformed, y_transformed) + args[2:]
        return self._ax.scatter(*args, **kwargs)

    def quiver(self, *args, **kwargs):
        """Intercept quiver to transform coordinates."""
        source_crs = self._remove_cartopy_kwargs(kwargs)
        if source_crs and len(args) >= 4:
            x_transformed, y_transformed = self._transform_coords(args[0], args[1], source_crs)
            args = (x_transformed, y_transformed) + args[2:]
        return self._ax.quiver(*args, **kwargs)

    def barbs(self, *args, **kwargs):
        """Intercept barbs to transform coordinates."""
        source_crs = self._remove_cartopy_kwargs(kwargs)
        if source_crs and len(args) >= 4:
            x_transformed, y_transformed = self._transform_coords(args[0], args[1], source_crs)
            args = (x_transformed, y_transformed) + args[2:]
        return self._ax.barbs(*args, **kwargs)

    def streamplot(self, *args, **kwargs):
        """Intercept streamplot to transform coordinates."""
        source_crs = self._remove_cartopy_kwargs(kwargs)
        if source_crs and len(args) >= 4:
            x_transformed, y_transformed = self._transform_coords(args[0], args[1], source_crs)
            args = (x_transformed, y_transformed) + args[2:]
        return self._ax.streamplot(*args, **kwargs)


class _TileFigure:
    """
    A minimal wrapper to make Tile compatible with Map's figure expectations.

    This class wraps a matplotlib Figure and GridSpec to provide the interface
    expected by the Map parent class.
    """

    def __init__(self, fig, gridspec):
        self.fig = fig
        self.gridspec = gridspec
        self.subplots = []

    def add_attribution(self, attribution):
        """Placeholder for attribution support."""
        pass

    def add_logo(self, logo):
        """Placeholder for logo support."""
        pass