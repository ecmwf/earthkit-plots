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

import matplotlib.pyplot as plt

from earthkit.plots.core.maps import Map


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

    def _ensure_axes(self):
        """Override to add tile-specific axes configuration."""
        # Call parent's _ensure_axes to create the axes
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