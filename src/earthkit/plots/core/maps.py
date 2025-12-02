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

import functools
import warnings

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.shapereader as shpreader
import matplotlib.patheffects as pe

from earthkit.plots.core.subplots import Subplot
from earthkit.plots.geo import coordinate_reference_systems, domains, natural_earth
from earthkit.plots.metadata.formatters import DimensionSetFormatter
from earthkit.plots.metadata.labels import CRS_NAMES
from earthkit.plots.schemas import schema
from earthkit.plots.sources import get_dimension_set
from earthkit.plots.utils import string_utils


def _reproject_geometries(geometries, src_crs, target_crs):
    """
    Reproject a list of shapely geometries from source CRS to target CRS.

    This is used as a performance optimization to avoid on-the-fly reprojection
    during matplotlib rendering. It's suitable for features with many small
    segments (like coastlines) but NOT for features with long straight lines
    that should be curved on the target projection (like political boundaries).

    Parameters
    ----------
    geometries : list
        List of shapely geometries to reproject.
    src_crs : cartopy.crs.CRS
        Source coordinate reference system.
    target_crs : cartopy.crs.CRS
        Target coordinate reference system.

    Returns
    -------
    list
        List of reprojected shapely geometries in target_crs.
    """
    import pyproj
    from shapely.ops import transform

    try:
        # Get proj4 strings for both CRS
        # Try proj4_init first, fall back to proj4_params
        src_proj = getattr(src_crs, 'proj4_init', None) or src_crs.proj4_params
        target_proj = getattr(target_crs, 'proj4_init', None) or target_crs.proj4_params

        # Create transformer
        transformer = pyproj.Transformer.from_crs(
            src_proj if isinstance(src_proj, str) else pyproj.CRS.from_proj4(src_proj),
            target_proj if isinstance(target_proj, str) else pyproj.CRS.from_proj4(target_proj),
            always_xy=True
        )

        # Reproject all geometries
        reprojected = []
        for geom in geometries:
            try:
                reprojected_geom = transform(transformer.transform, geom)
                if not reprojected_geom.is_empty:
                    reprojected.append(reprojected_geom)
            except Exception as e:
                # If a single geometry fails, warn but continue with others
                warnings.warn(
                    f"Failed to reproject geometry: {e}. Skipping this geometry.",
                    RuntimeWarning
                )
                continue

        return reprojected

    except Exception as e:
        # If reprojection fails entirely, warn and return original geometries
        warnings.warn(
            f"Geometry reprojection failed: {e}. Falling back to cartopy reprojection.",
            RuntimeWarning
        )
        return geometries


def _step_range(bounds, step, ref=0):
    """
    Generate a range of values with a given step size and reference point.

    Parameters
    ----------
    bounds : list
        The [min, max] bounds for the range.
    step : float
        The step size.
    ref : float, optional
        The reference point to align steps to. Default is 0.

    Returns
    -------
    list
        List of values within bounds, aligned to the reference point.
    """
    import numpy as np

    min_val, max_val = bounds
    # Calculate the starting point aligned with reference
    start = ref + np.ceil((min_val - ref) / step) * step
    # Generate the range
    return list(np.arange(start, max_val + step/2, step))


def queue_if_no_axes(method):
    """
    Decorator for Map methods that should be queued if axes don't exist yet.

    This allows methods like coastlines(), gridlines(), etc. to be called before
    data is plotted. They will be queued and executed once the CRS is determined.
    """
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if self._ax is None and not self._crs_explicit:
            # Queue the method call for later execution
            self._method_queue.append((method.__name__, args, kwargs))
            return None
        else:
            # Execute immediately
            return method(self, *args, **kwargs)
    return wrapper


class Map(Subplot):
    """
    A specialized Subplot for plotting geospatial data.

    Parameters
    ----------
    row : int, optional
        The row index of the subplot in the figure.
    column : int, optional
        The column index of the subplot in the figure.
    figure : Figure, optional
        The Figure to which the subplot belongs.
    domain : str, tuple, list or Domain, optional
        The domain of the map. Can be a string, a tuple or a list of
        coordinates, or a :class:`earthkit.plots.geo.domains.Domain` object. This is used to set the extent and
        projection of the map.
    domain_crs : cartopy.crs.CRS, optional
        The CRS of the domain extents when domain is provided as a tuple or list of coordinates.
        If None (default), assumes PlateCarree (regular latitude/longitude). Only used when
        domain is a tuple or list of numeric coordinates.
    crs : cartopy.crs.CRS, optional
        The CRS of the map. If not provided, it will be inferred from the
        domain. See https://cartopy.readthedocs.io/stable/reference/projections.html#cartopy-projections for a list of available CRSs.
    **kwargs
        Additional keyword arguments to pass to the :class:`matplotlib.axes.Axes` object.
    """

    def __init__(self, *args, domain=None, domain_crs=None, crs=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Track whether CRS was explicitly set by user
        self._crs_explicit = crs is not None or domain is not None
        self._crs_inferred = False

        # Parse CRS if provided as string
        if isinstance(crs, str):
            crs = coordinate_reference_systems.parse_crs(crs)

        # Set default domain_crs to PlateCarree if not provided
        # Note: domain_crs can be a string (e.g., "EPSG:32661") and will be
        # parsed by BoundingBox.from_bbox() / Domain.from_bbox()
        if domain_crs is None:
            domain_crs = ccrs.PlateCarree()

        if domain is None:
            self.domain = domain
            self._crs = crs
        else:
            if isinstance(domain, (list, tuple)):
                if isinstance(domain[0], str):
                    self.domain = domains.union(domain)
                else:
                    # domain_crs and crs will be parsed by Domain.from_bbox()
                    self.domain = domains.Domain.from_bbox(
                        bbox=domain,
                        source_crs=domain_crs,
                        target_crs=crs,
                    )
            elif isinstance(domain, str):
                self.domain = domains.Domain.from_string(domain, crs=crs)
            elif isinstance(domain, domains.Domain):
                self.domain = domain
            if crs is not None:
                self._crs = coordinate_reference_systems.parse_crs(crs)
            else:
                self._crs = self.domain.bbox.crs

        self.natural_earth_resolution = "medium"

        # Queue for methods that need axes but were called before axes creation
        self._method_queue = []

    @property
    def crs(self):
        """The coordinate reference system of the map."""
        if self._crs is not None:
            return self._crs
        elif self.domain is not None:
            return self.domain.bbox.crs
        elif self._crs is None:
            return ccrs.PlateCarree()

    @property
    def crs_name(self):
        """The human-readable name of the coordinate reference system of the map."""
        class_name = self.crs.__class__.__name__
        return CRS_NAMES.get(
            class_name,
            " ".join(string_utils.split_camel_case(class_name)),
        )

    @property
    def domain_name(self):
        """The human-readable name of the domain of the map."""
        if self.domain is not None:
            name = self.domain.title
        else:
            name = "None"
        if name == "None":
            if self.domain is not None:
                if self.domain.crs.__class__.__name__ == "PlateCarree":
                    extent = self.ax.get_extent()
                    if extent == (-180.0, 180.0, -90.0, 90.0):
                        name = "Global"
                    else:
                        name = domains.bounds.to_string(extent)
        return name

    def _get_or_create_yaxis(self, units):
        """
        Override parent method to reject multi-axis behavior on Maps.

        Maps should not support multiple y-axes as they are geographic plots
        where the y-axis represents latitude, not data values.

        Parameters
        ----------
        units : str or None
            The units for the y-axis (ignored for Maps).

        Returns
        -------
        matplotlib.axes.Axes
            Always returns the primary axis.

        Raises
        ------
        ValueError
            If attempting to create a second y-axis with different units.
        """
        # For Maps, always use the primary axis
        # But check if we're trying to create multiple axes with different units
        if len(self._yaxes) > 0:
            # We already have an axis registered
            existing_units = list(self._yaxes.keys())[0]
            if existing_units != units:
                from earthkit.plots.metadata import units as metadata_units
                # Check if units are actually different
                if not (existing_units is None and units is None):
                    if existing_units is None or units is None:
                        # One is None, the other isn't
                        raise ValueError(
                            "Multi-axis plotting is not supported on Map objects. "
                            "All data plotted on a Map must have compatible units or no units. "
                            f"Attempted to mix units: {existing_units} and {units}."
                        )
                    elif not metadata_units.are_equal(existing_units, units):
                        raise ValueError(
                            "Multi-axis plotting is not supported on Map objects. "
                            "All data plotted on a Map must have compatible units. "
                            f"Attempted to mix incompatible units: {existing_units} and {units}."
                        )

        # Register the primary axis if not already registered
        if units not in self._yaxes:
            self._yaxes[units] = (self.ax, 'left', 0)

        return self.ax

    def _infer_crs_from_data(self, dimension_set):
        """
        Infer CRS from data if not explicitly set by user.

        Parameters
        ----------
        dimension_set : DimensionSet
            The dimension set from the first data being plotted.
        """
        if self._crs_explicit or self._crs_inferred:
            return  # CRS already determined

        # Try to get CRS from dimension_set
        data_crs = dimension_set.crs
        if data_crs is not None:
            self._crs = data_crs
            self._crs_inferred = True

    def _ensure_axes(self):
        """
        Ensure axes exist, creating them with appropriate CRS if needed.
        If CRS was not explicitly set and not inferred from data, use PlateCarree.
        """
        if self._ax is not None:
            return  # Axes already exist

        # If CRS still not set, use PlateCarree as default
        if self._crs is None and not self._crs_explicit:
            self._crs = ccrs.PlateCarree()

        # Create the axes
        self._ax = self.figure.fig.add_subplot(
            self.figure.gridspec[self.row, self.column],
            projection=self.crs,
            **self._ax_kwargs,
        )

        # Set domain extent if specified
        if self.domain is not None and None not in list(self.domain.bbox):
            self._ax.set_extent(
                self.domain.bbox.to_cartopy_bounds(),
                self.domain.bbox.crs,
            )

        # Replay queued method calls
        self._replay_method_queue()

    def _replay_method_queue(self):
        """Execute all queued method calls now that axes exist."""
        for method_name, args, kwargs in self._method_queue:
            # Get the method and call it - it will execute now that axes exist
            method = getattr(self, method_name)
            # Get the underlying unwrapped method to avoid queuing again
            if hasattr(method, '__wrapped__'):
                method = method.__wrapped__.__get__(self, type(self))
            method(*args, **kwargs)
        self._method_queue.clear()

    @property
    def ax(self):
        """The :class:`matplotlib.axes.Axes` object of the subplot."""
        self._ensure_axes()
        return self._ax

    def _on_first_data_plot(self, dimension_set):
        """
        Called when data is first plotted on this map.
        Used to infer CRS from data if not explicitly set.

        Parameters
        ----------
        dimension_set : DimensionSet
            The dimension set being plotted.
        """
        if self._ax is None:  # Haven't created axes yet
            self._infer_crs_from_data(dimension_set)

    def _plot_kwargs(self, *args, **kwargs):
        """
        Get plot kwargs for matplotlib methods on maps.

        Returns
        -------
        dict
            Dictionary of keyword arguments to pass to matplotlib plotting methods.
            For maps, the 'transform' parameter is set by the extractors based on
            the data's CRS from the dimension_set.
        """
        # The transform will be set by the extractors based on dimension_set.crs
        # No need to set a default here
        return kwargs

    # @schema.grid_points.apply()
    # def grid_points(self, *args, **kwargs):
    #     """
    #     Plot grid point centroids on the map.

    #     Parameters
    #     ----------
    #     data : xarray.DataArray or earthkit.data.core.Base, optional
    #         The data source for which to plot grid_points.
    #     x : str, optional
    #         The name of the x-coordinate variable in the data source.
    #     y : str, optional
    #         The name of the y-coordinate variable in the data source.
    #     **kwargs
    #         Additional keyword arguments to pass to :func:`matplotlib.pyplot.scatter`.
    #     """
    #     popped_kwargs = []
    #     for key in ["style", "levels", "units", "colors"]:
    #         if key in kwargs:
    #             popped_kwargs.append(key)
    #             kwargs.pop(key)
    #     return self.scatter(*args, **kwargs)

    def labels(self, data=None, label=None, x=None, y=None, **kwargs):
        """
        Plot labels on the map.

        Parameters
        ----------
        data : xarray.DataArray or earthkit.data.core.Base, optional
            The data source for which to plot labels.
        label : str, optional
            The label to plot.
        x : str, optional
            The name of the x-coordinate variable in the data source.
        y : str, optional
            The name of the y-coordinate variable in the data source.
        **kwargs
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.annotate`.
        """
        from earthkit.plots.sources.core import PlotType

        dimension_set = get_dimension_set(
            data,
            x=x if x is not None else "auto",
            y=y if y is not None else "auto",
            plot_type=PlotType.GEOGRAPHIC_1D,
        )
        labels = DimensionSetFormatter(dimension_set).format(label)
        crs = dimension_set.crs or ccrs.PlateCarree()
        for label, x_val, y_val in zip(labels, dimension_set.x.values, dimension_set.y.values):
            self.ax.annotate(label, (x_val, y_val), transform=crs, **kwargs)

    @schema.point_cloud.apply()
    def point_cloud(self, *args, **kwargs):
        """
        Plot a point cloud on the map.

        Parameters
        ----------
        data : xarray.DataArray or earthkit.data.core.Base, optional
            The data source for which to plot grid_points.
        x : str, optional
            The name of the x-coordinate variable in the data source.
        y : str, optional
            The name of the y-coordinate variable in the data source.
        units : str, optional
            The units to convert the data to. Relies on well-formatted metadata to understand the units of your input data.
        **kwargs
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.scatter`.
        """
        return self.scatter(*args, **kwargs)

    def _add_polygon_labels(
        self,
        records,
        x_key=None,
        y_key=None,
        label_key=None,
        adjust_labels=False,
    ):
        label_kwargs = dict()
        label_kwargs = {
            **dict(
                ha="center",
                va="center",
                path_effects=[pe.withStroke(linewidth=1.5, foreground="#555555")],
                fontsize=9,
                weight="bold",
                color=(0.95, 0.95, 0.95),
                clip_on=True,
                clip_box=self.ax.bbox,
                transform=ccrs.Geodetic(),
            ),
            **label_kwargs,
        }

        if label_key is None:
            for label_key in records[0].attributes:
                if "name" in label_key.lower():
                    break

        texts = []
        for record in records:
            name = record.attributes[label_key]

            if record.geometry.__class__.__name__ == "MultiPolygon":
                centroid = max(record.geometry.geoms, key=lambda a: a.area).centroid
            else:
                centroid = record.geometry.centroid
            x = centroid.x
            y = centroid.y
            if x_key in record.attributes:
                x = record.attributes[x_key]
            if y_key in record.attributes:
                y = record.attributes[y_key]

            text = self.ax.text(x, y, name, **label_kwargs)
            texts.append(text)
        if adjust_labels:
            from adjustText import adjust_text

            adjust_text(texts)
        return texts

    def natural_earth_layer(
        category,
        name,
        default_attribute="NAME_LONG",
        default_label="NAME_LONG",
        max_resolution="high",
        min_resolution="low",
        line=False,
        default_transform_first=False,
    ):
        """
        Decorate a method to add a natural earth layer to the map.

        Parameters
        ----------
        category : str
            The category of the natural earth layer.
        name : str
            The name of the natural earth layer.
        default_attribute : str, optional
            The attribute of the natural earth layer to use as the default label.
        default_label : str, optional
            The label to use for the natural earth layer.
        max_resolution : str, optional
            The maximum resolution of the natural earth layer.
        min_resolution : str, optional
            The minimum resolution of the natural earth layer.
        line : bool, optional
            Whether to plot the natural earth layer as a line.
        default_transform_first : bool, optional
            Default value for transform_first parameter. If True, reproject
            geometries before plotting for better performance. If False, let
            cartopy handle reprojection (needed for long straight lines that
            should be curved on the projection). Default is False.
        """

        def decorator(method):
            @functools.wraps(method)
            def wrapper(
                self,
                *args,
                resolution=None,
                include=None,
                exclude=None,
                labels=False,
                special_styles=None,
                adjust_labels=False,
                transform_first=None,  # Allow user override
                **kwargs,
            ):
                # Use decorator default if user didn't specify
                _transform_first = default_transform_first if transform_first is None else transform_first
                if resolution is None:
                    resolution = self.natural_earth_resolution
                resolution = natural_earth.get_resolution(
                    resolution,
                    self.ax,
                    self.crs,
                    max_resolution,
                    min_resolution,
                )

                if line:
                    if "color" in kwargs:
                        kwargs["edgecolor"] = kwargs.pop("color")

                shape_name = name
                if isinstance(name, dict):
                    shape_name = name[resolution]

                shpfilename = shpreader.natural_earth(
                    resolution=resolution,
                    category=category,
                    name=shape_name,
                )
                reader = shpreader.Reader(shpfilename)

                records = list(reader.records())

                filtered_records = []
                special_records = []

                if special_styles is not None:
                    for record in records:
                        for style in special_styles:
                            if (
                                record.attributes.get(style["key"], None)
                                in style["values"]
                            ):
                                special_records.append([record, style["kwargs"]])
                            else:
                                filtered_records.append(record)
                else:
                    filtered_records = list(reader.records())

                if include is not None or exclude is not None:
                    exclude = (
                        [exclude]
                        if not (isinstance(exclude, (list, tuple)) or exclude is None)
                        else exclude
                    )
                    include = (
                        [include]
                        if not (isinstance(include, (list, tuple)) or include is None)
                        else include
                    )

                    filtered_records = [
                        record
                        for record in records
                        if (
                            (
                                include is None
                                or record.attributes.get(default_attribute) in include
                            )
                            and (
                                exclude is None
                                or record.attributes.get(default_attribute)
                                not in exclude
                            )
                        )
                    ]

                if labels:
                    if not isinstance(labels, str):
                        labels = default_label
                    self._add_polygon_labels(
                        filtered_records,
                        x_key="LABEL_X",
                        y_key="LABEL_Y",
                        label_key=labels,
                        adjust_labels=adjust_labels,
                    )

                geometries = []
                for record in filtered_records:
                    geom = record.geometry

                    if not geom.is_empty:  # Only keep visible parts
                        geometries.append(geom)

                # Determine source and target CRS for features
                src_crs = ccrs.PlateCarree()
                target_crs = self.crs

                # Apply transform_first optimization if requested and needed
                if _transform_first and target_crs != src_crs:
                    # Reproject geometries before adding to map for better performance
                    geometries = _reproject_geometries(geometries, src_crs, target_crs)
                    feature_crs = target_crs
                else:
                    # Let cartopy handle reprojection (needed for proper line interpolation)
                    feature_crs = src_crs

                # Add optimized features
                feature = cfeature.ShapelyFeature(geometries, feature_crs)
                result = self.ax.add_feature(feature, *args, **kwargs)

                if special_styles is not None:
                    for record, style in special_records:
                        geom = record.geometry
                        if not geom.is_empty:
                            # Special styled features also respect transform_first
                            if _transform_first and target_crs != src_crs:
                                geom_list = _reproject_geometries([geom], src_crs, target_crs)
                                feature = cfeature.ShapelyFeature(geom_list, target_crs)
                            else:
                                feature = cfeature.ShapelyFeature([geom], src_crs)
                            self.ax.add_feature(feature, *args, **{**kwargs, **style})

                return result

            return wrapper

        return decorator

    @queue_if_no_axes
    @schema.coastlines.apply()
    @natural_earth_layer("physical", "coastline", line=True, default_transform_first=True)
    def coastlines(self, *args, **kwargs):
        """Add coastlines from Natural Earth.

        Coastlines use optimized reprojection for better performance on
        non-PlateCarree projections.

        Parameters
        ----------
        resolution: (str, optional)
            One of "low", "medium" or "high", or a named resolution from the
            Natural Earth dataset.
        transform_first: (bool, optional)
            If True, reproject geometries before plotting for better performance.
            If False, let cartopy handle reprojection. Default is True for coastlines.
        """

    @queue_if_no_axes
    @schema.borders.apply()
    @natural_earth_layer("cultural", "admin_0_boundary_lines_land", line=True)
    def borders(self, *args, **kwargs):
        """Add country boundary polygons from Natural Earth.

        Parameters
        ----------
        resolution: (str, optional)
            One of "low", "medium" or "high", or a named resolution from the
            Natural Earth dataset.
        transform_first: (bool, optional)
            If True, reproject geometries before plotting. If False (default),
            let cartopy handle reprojection to properly interpolate long straight lines.
        """

    @queue_if_no_axes
    @schema.unit_boundaries.apply()
    @natural_earth_layer(
        "cultural",
        name={
            "10m": "admin_0_boundary_lines_map_units",
            "50m": "admin_0_boundary_map_units",
        },
        min_resolution="medium",
        line=True,
    )
    def unit_boundaries(self, *args, **kwargs):
        """Add country boundary polygons from Natural Earth.

        Parameters
        ----------
        resolution: (str, optional)
            One of "low", "medium" or "high", or a named resolution from the
            Natrual Earth dataset.
        """

    @queue_if_no_axes
    @schema.disputed_boundaries.apply()
    @natural_earth_layer(
        "cultural",
        name={
            "10m": "admin_0_disputed_areas",
            "50m": "admin_0_breakaway_disputed_areas",
        },
        min_resolution="medium",
        line=True,
    )
    def disputed_boundaries(self, *args, **kwargs):
        """Add country boundary polygons from Natural Earth.

        Parameters
        ----------
        resolution: (str, optional)
            One of "low", "medium" or "high", or a named resolution from the
            Natrual Earth dataset.
        """

    @queue_if_no_axes
    @schema.administrative_areas.apply()
    @natural_earth_layer(
        "cultural",
        "admin_1_states_provinces",
        default_attribute="name",
        default_label="name",
        line=True,
    )
    def administrative_areas(self, *args, **kwargs):
        """Add country boundary polygons from Natural Earth.

        Parameters
        ----------
        resolution: (str, optional)
            One of "low", "medium" or "high", or a named resolution from the
            Natrual Earth dataset.
        """

    @queue_if_no_axes
    @schema.countries.apply()
    @natural_earth_layer("cultural", "admin_0_countries", default_label="ISO_A2_EH")
    def countries(self, *args, **kwargs):
        """Add country boundary polygons from Natural Earth.

        Parameters
        ----------
        resolution: (str, optional)
            One of "low", "medium" or "high", or a named resolution from the
            Natrual Earth dataset.
        """

    @queue_if_no_axes
    @schema.land.apply()
    @natural_earth_layer("physical", "land")
    def land(self, *args, **kwargs):
        """Add country boundary polygons from Natural Earth.

        Parameters
        ----------
        resolution: (str, optional)
            One of "low", "medium" or "high", or a named resolution from the
            Natrual Earth dataset.
        """

    @queue_if_no_axes
    @schema.ocean.apply()
    @natural_earth_layer("physical", "ocean")
    def ocean(self, *args, **kwargs):
        """Add country boundary polygons from Natural Earth.

        Parameters
        ----------
        resolution: (str, optional)
            One of "low", "medium" or "high", or a named resolution from the
            Natrual Earth dataset.
        """

    @queue_if_no_axes
    @schema.urban_areas.apply()
    @natural_earth_layer("cultural", "urban_areas")
    def urban_areas(self, *args, **kwargs):
        """Add country boundary polygons from Natural Earth.

        Parameters
        ----------
        resolution: (str, optional)
            One of "low", "medium" or "high", or a named resolution from the
            Natrual Earth dataset.
        """

    @queue_if_no_axes
    @schema.countries.apply()
    @natural_earth_layer("cultural", "admin_0_map_units", default_label="ADM0_TLC")
    def map_units(self, *args, **kwargs):
        """Add country boundary polygons from Natural Earth.

        Parameters
        ----------
        resolution: (str, optional)
            One of "low", "medium" or "high", or a named resolution from the
            Natrual Earth dataset.
        """

    @queue_if_no_axes
    def cities(
        self,
        density=None,
        labels=True,
        capital_cities=False,
        capital_cities_kwargs=None,
        medium_cities_kwargs=None,
        small_cities_kwargs=None,
        adjust_labels=False,
        **kwargs,
    ):
        """
        Add city markers to the map.

        Parameters
        ----------
        density : str or int, optional
            The resolution of the Natural Earth dataset to use. Can be one of
            "low", "medium" or "high".
        labels : bool, optional
            Whether to add city names as labels. Default is True.
        capital_cities : bool, optional
            Whether to include capital cities only. Default is False.
        capital_cities_kwargs : dict, optional
            Keyword arguments to pass to the scatter method for capital cities.
        medium_cities_kwargs : dict, optional
            Keyword arguments to pass to the scatter method for medium cities.
        small_cities_kwargs : dict, optional
            Keyword arguments to pass to the scatter method for small cities.
        adjust_labels : bool, optional
            Whether to adjust the positions of city labels to avoid overlap.
            Default is False. Note that this adjustment can be slow for large
            numbers of labels.
        **kwargs
            Additional keyword arguments to pass to the scatter method.
        """
        if density is None:
            density = self.natural_earth_resolution
        density = natural_earth.get_resolution(density, self.ax, self.crs)

        if capital_cities_kwargs is None:
            capital_cities_kwargs = (
                kwargs or natural_earth.DEFAULT_CAPITAL_CITIES_KWARGS
            )
        if medium_cities_kwargs is None:
            medium_cities_kwargs = kwargs or natural_earth.DEFAULT_MEDIUM_CITIES_KWARGS
        if small_cities_kwargs is None:
            small_cities_kwargs = kwargs or natural_earth.DEFAULT_SMALL_CITIES_KWARGS

        fname = shpreader.natural_earth(
            resolution=density,
            category="cultural",
            name="populated_places",
        )
        reader = shpreader.Reader(fname)
        records = list(reader.records())

        texts = []
        for record in records:
            if capital_cities and not record.attributes["ADM0CAP"]:
                continue
            if self.domain.bbox.contains_point(
                (record.geometry.x, record.geometry.y),
                crs=ccrs.PlateCarree(),
            ):
                scatter_kwargs = medium_cities_kwargs
                if record.attributes["ADM0CAP"]:
                    scatter_kwargs = capital_cities_kwargs
                elif record.attributes["RANK_MAX"] < 8:
                    scatter_kwargs = small_cities_kwargs
                text_kwargs = scatter_kwargs.get("text", dict())
                self.ax.scatter(
                    record.geometry.x,
                    record.geometry.y,
                    transform=ccrs.PlateCarree(),
                    zorder=10,
                    **{k: v for k, v in scatter_kwargs.items() if k != "text"},
                )
                if labels:
                    text = self.ax.text(
                        record.geometry.x,
                        record.geometry.y,
                        record.attributes["NAME_EN"],
                        transform=ccrs.PlateCarree(),
                        clip_on=True,
                        zorder=10,
                        **text_kwargs,
                    )
                    texts.append(text)
        if adjust_labels:
            from adjustText import adjust_text

            adjust_text(texts)
        return texts

    @queue_if_no_axes
    def stock_img(self, *args, **kwargs):
        """
        Add the cartopy stock image to the map.

        Parameters
        ----------
        *args
            Positional arguments to pass to the stock_img method.
        **kwargs
            Keyword arguments to pass to the stock_img method.
        """
        self.ax.stock_img(*args, **kwargs)

    @queue_if_no_axes
    def image(self, img, extent, origin="upper", transform=ccrs.PlateCarree()):
        """
        Add an image to the map.

        Parameters
        ----------
        img : str or PIL.Image
            The image to add to the map.
        extent : tuple
            The extent of the image in the form (xmin, xmax, ymin, ymax).
        origin : str, optional
            The origin of the image. Default is "upper".
        transform : cartopy.crs.CRS, optional
            The CRS of the image. Default is PlateCarree (euirectangular).
        """
        if isinstance(img, str):
            import PIL

            img = PIL.Image.open(img)
        return self.ax.imshow(img, origin=origin, extent=extent, transform=transform)

    @queue_if_no_axes
    @schema.shapes.apply()
    def shapes(
        self,
        shapes,
        *args,
        transform=ccrs.PlateCarree(),
        adjust_labels=False,
        labels=False,
        **kwargs,
    ):
        """
        Add shapes to the map.

        Parameters
        ----------
        shapes : str or cartopy.io.shapereader.Reader
            The shapes to add to the map. Can be a path to a shapefile or a
            cartopy Reader object.
        *args
            Positional arguments to pass to the add_geometries method.
        transform : cartopy.crs.CRS, optional
            The CRS of the shapes. Default is PlateCarree.
        adjust_labels : bool, optional
            Whether to adjust the positions of shape labels to avoid overlap.
            Default is False. Note that this adjustment can be slow for large
            numbers of labels.
        labels : str, optional
            The attribute of the shapes to use as labels. Default is False.
        **kwargs
            Additional keyword arguments to pass to the add_geometries method.
        """
        if isinstance(shapes, str):
            shapes = shpreader.Reader(shapes)
        results = self.ax.add_geometries(
            shapes.geometries(), transform, *args, **kwargs
        )
        if labels:
            label_key = labels if isinstance(labels, str) else None
            self._add_polygon_labels(
                list(shapes.records()), label_key=label_key, adjust_labels=adjust_labels
            )
        return results

    @queue_if_no_axes
    @schema.gridlines.apply()
    def gridlines(self, *args, xstep=None, xref=0, ystep=None, yref=0, **kwargs):
        """
        Add gridlines to the map.

        Parameters
        ----------
        *args
            Positional arguments to pass to cartopy.mpl.gridliner.Gridliner.
        xstep : float, optional
            The step size for the x-axis gridlines. Default is None.
        xref : float, optional
            The reference point for the xstep. Default is 0.
        ystep : float, optional
            The step size for the y-axis gridlines. Default is None.
        yref : float, optional
            The reference point for the ystep. Default is 0.
        **kwargs
            Additional keyword arguments to pass to cartopy.mpl.gridliner.Gridliner.
        """
        if xstep is not None:
            kwargs["xlocs"] = _step_range([-180, 180], xstep, xref)
        if ystep is not None:
            kwargs["ylocs"] = _step_range([-90, 90], ystep, yref)
        self.ax.gridlines(*args, **kwargs)

    def standard_layers(self):
        """
        Add standard map layers to the map.

        This method adds the following layers to the map:
        - land
        - coastlines
        - borders
        - gridlines
        """
        self.land()
        self.coastlines()
        self.borders()
        self.gridlines()
