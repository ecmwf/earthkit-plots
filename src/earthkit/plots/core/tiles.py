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
        The DPI to use for rendering. Default is 100.
    **kwargs
        Additional keyword arguments to pass to the :class:`Map` constructor.

    Examples
    --------
    >>> tile = Tile(domain=[-10, 50, 35, 70], size=(512, 512))
    >>> tile.coastlines()
    >>> tile.save("tile.png")
    """

    def __init__(self, size=(256, 256), dpi=100, **kwargs):
        self._pixel_size = size
        self._dpi = dpi
        print("foo")

        # Create a standalone figure for this tile
        # Convert pixel size to inches based on DPI
        figsize = (size[0] / dpi, size[1] / dpi)

        # Initialize parent Map with figure and gridspec references
        # We need to pass a figure-like object, so we create a minimal wrapper
        super().__init__(size=figsize, **kwargs)

    # @property
    # def ax(self):
    #     """The matplotlib axes object for the tile."""
    #     if self._ax is None:
    #         # Create axes with the tile's CRS
    #         self._ax = self._fig.add_subplot(
    #             self._gridspec[0, 0],
    #             projection=self.crs,
    #             **self._ax_kwargs,
    #         )

    #         # Set domain extent if specified
    #         if self.domain is not None and None not in list(self.domain.bbox):
    #             self._ax.set_extent(
    #                 self.domain.bbox.to_cartopy_bounds(),
    #                 self.domain.bbox.crs,
    #             )

    #         # Make axes background transparent
    #         self._ax.patch.set_alpha(0)

    #         # Remove any margins
    #         self._ax.set_aspect('auto')

    #         # Replay queued method calls from parent Map class
    #         self._replay_method_queue()

    #     return self._ax

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
        super().save(filename, **kwargs)

    def show(self):
        """
        Display the tile.

        This calls :func:`matplotlib.pyplot.show` to display the tile.
        """
        plt.show()


# class TileFigure:
#     """
#     A minimal wrapper to make Tile compatible with Map's figure expectations.

#     This class wraps a matplotlib Figure and GridSpec to provide the interface
#     expected by the Map parent class.
#     """

#     def __init__(self, fig, gridspec):
#         self.fig = fig
#         self.gridspec = gridspec
#         self.subplots = []
