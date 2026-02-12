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

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.shapereader as shpreader
import matplotlib.patheffects as pe

from earthkit.plots.components.subplots import Subplot
from earthkit.plots.geo import coordinate_reference_systems, domains, natural_earth
from earthkit.plots.metadata.formatters import SourceFormatter
from earthkit.plots.metadata.labels import CRS_NAMES
from earthkit.plots.schemas import schema
from earthkit.plots.sources import get_source
from earthkit.plots.styles.levels import step_range
from earthkit.plots.utils import string_utils


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
    crs : cartopy.crs.CRS, optional
        The CRS of the map. If not provided, it will be inferred from the
        domain. See https://cartopy.readthedocs.io/stable/reference/projections.html#cartopy-projections for a list of available CRSs.
    **kwargs
        Additional keyword arguments to pass to the :class:`matplotlib.axes.Axes` object.
    """

    def __init__(self, *args, domain=None, crs=None, **kwargs):
        super().__init__(*args, **kwargs)
        if isinstance(crs, str):
            crs = coordinate_reference_systems.parse_crs(crs)
        if domain is None:
            self.domain = domain
            self._crs = crs
        else:
            if isinstance(domain, (list, tuple)):
                if isinstance(domain[0], str):
                    self.domain = domains.union(domain)
                else:
                    self.domain = domains.Domain.from_bbox(
                        bbox=domain,
                        source_crs=ccrs.PlateCarree(),
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

    @property
    def ax(self):
        """The :class:`matplotlib.axes.Axes` object of the subplot."""
        if self._ax is None:
            self._ax = self.figure.fig.add_subplot(
                self.figure.gridspec[self.row, self.column],
                projection=self.crs,
                **self._ax_kwargs,
            )
            if self.domain is not None and None not in list(self.domain.bbox):
                self._ax.set_extent(
                    self.domain.bbox.to_cartopy_bounds(),
                    self.domain.bbox.crs,
                )
        return self._ax

    def _plot_kwargs(self, source):
        if self._crs is None:
            self._crs = source.crs or ccrs.PlateCarree()
        return {"transform": source.crs or ccrs.PlateCarree()}

    @schema.grid_points.apply()
    def grid_points(self, *args, **kwargs):
        """
        Plot grid point centroids on the map.

        Parameters
        ----------
        data : xarray.DataArray or earthkit.data.core.Base, optional
            The data source for which to plot grid_points.
        x : str, optional
            The name of the x-coordinate variable in the data source.
        y : str, optional
            The name of the y-coordinate variable in the data source.
        **kwargs
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.scatter`.
        """
        popped_kwargs = []
        for key in ["style", "levels", "units", "colors"]:
            if key in kwargs:
                popped_kwargs.append(key)
                kwargs.pop(key)
        return self.scatter(*args, **kwargs)

    def gridpoints(self, *args, **kwargs):
        """
        Plot grid point centroids on the map.

        Deprecated: Use :meth:`grid_points` instead.

        Parameters
        ----------
        data : xarray.DataArray or earthkit.data.core.Base, optional
            The data source for which to plot grid_points.
        x : str, optional
            The name of the x-coordinate variable in the data source.
        y : str, optional
            The name of the y-coordinate variable in the data source.
        **kwargs
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.scatter`.
        """
        import warnings

        warnings.warn(
            "gridpoints is deprecated and will be removed in earthkit-plots 0.6. "
            "Please use grid_points instead."
        )
        return self.grid_points(*args, **kwargs)

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
        source = get_source(data=data, x=x, y=y)
        labels = SourceFormatter(source).format(label)
        crs = source.crs or ccrs.PlateCarree()
        for label, x, y in zip(labels, source.x.values, source.y.values):
            self.ax.annotate(label, (x, y), transform=crs, **kwargs)

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

    def ancillary_layer(
        sources,
        line=False,
        max_resolution="high",
        min_resolution="low",
        default_transform_first=False,
    ):
        """
        Decorate a method to add ancillary geographic layers from various data sources.

        Parameters
        ----------
        sources : dict
            Configuration dictionary where keys are source names (e.g., "natural_earth", "gisco")
            and values are dictionaries containing source-specific configuration:

            For "natural_earth":
                - category: str - The Natural Earth category (e.g., "cultural", "physical")
                - name: str or dict - The layer name, or dict mapping resolutions to names
                - attribute: str - Default attribute for filtering (e.g., "NAME_LONG")
                - label: str - Default label attribute (e.g., "ISO_A2_EH")

            For "gisco":
                - geometry_type: str - GISCO geometry type ("polygons", "lines", "points")
                - attribute: str - Default attribute for filtering (e.g., "NAME_EN")
                - label: str - Default label attribute (e.g., "CNTR")

        line : bool, optional
            Whether to plot the layer as lines. Default is False.
        max_resolution : str, optional
            Maximum resolution for Natural Earth data. Default is "high".
        min_resolution : str, optional
            Minimum resolution for Natural Earth data. Default is "low".
        default_transform_first : bool, optional
            Default value for transform_first parameter. If True, reproject
            geometries before plotting for better performance. If False, let
            cartopy handle reprojection. Default is False.

        Examples
        --------
        >>> @ancillary_layer(
        ...     sources={
        ...         "natural_earth": {
        ...             "category": "cultural",
        ...             "name": "admin_0_countries",
        ...             "attribute": "NAME_LONG",
        ...             "label": "ISO_A2_EH",
        ...         },
        ...         "gisco": {
        ...             "geometry_type": "polygons",
        ...             "attribute": "NAME_EN",
        ...             "label": "CNTR",
        ...         },
        ...     },
        ...     default_transform_first=True,
        ... )
        ... def countries(self, *args, **kwargs):
        ...     pass
        """

        def decorator(method):
            @functools.wraps(method)
            def wrapper(
                self,
                *args,
                source="natural_earth",
                resolution=None,
                include=None,
                exclude=None,
                labels=False,
                special_styles=None,
                adjust_labels=False,
                transform_first=None,
                **kwargs,
            ):
                _transform_first = (
                    default_transform_first
                    if transform_first is None
                    else transform_first
                )

                if source not in sources:
                    raise ValueError(
                        f"source='{source}' is not supported for this method. "
                        f"Valid sources are: {list(sources.keys())}"
                    )

                source_config = sources[source]

                # Set default resolution
                if resolution is None:
                    resolution = self.natural_earth_resolution

                # Load data using source-specific loader
                if source == "gisco":
                    from earthkit.plots.geo import gisco

                    records_list, attribute_key, label_key = gisco.load_layer(
                        source_config, resolution
                    )
                    self.figure.add_attribution(
                        "© EuroGeographics for the administrative boundaries"
                    )

                elif source == "natural_earth":
                    records_list, attribute_key, label_key = natural_earth.load_layer(
                        source_config,
                        resolution,
                        self.ax,
                        self.crs,
                        max_resolution,
                        min_resolution,
                    )

                # Common processing for both sources
                if line:
                    if "color" in kwargs:
                        kwargs["edgecolor"] = kwargs.pop("color")

                filtered_records = []
                special_records = []

                if special_styles is not None:
                    for record in records_list:
                        for style in special_styles:
                            if (
                                record.attributes.get(style["key"], None)
                                in style["values"]
                            ):
                                special_records.append([record, style["kwargs"]])
                            else:
                                filtered_records.append(record)
                else:
                    filtered_records = records_list

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
                        for record in records_list
                        if (
                            (
                                include is None
                                or record.attributes.get(attribute_key) in include
                            )
                            and (
                                exclude is None
                                or record.attributes.get(attribute_key) not in exclude
                            )
                        )
                    ]

                if labels:
                    if not isinstance(labels, str):
                        labels = label_key
                    # Use different label position keys depending on source
                    if source == "gisco":
                        # GISCO may not have label positions, use centroid
                        self._add_polygon_labels(
                            filtered_records,
                            x_key=None,  # Will compute from geometry
                            y_key=None,
                            label_key=labels,
                            adjust_labels=adjust_labels,
                        )
                    else:
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
                    from earthkit.plots.geo.geometry import reproject_geometries

                    # Reproject geometries before adding to map for better performance
                    geometries = reproject_geometries(geometries, src_crs, target_crs)
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
                            feature = cfeature.ShapelyFeature([geom], self.crs)
                            self.ax.add_feature(feature, *args, **{**kwargs, **style})

                return result

            return wrapper

        return decorator

    @schema.coastlines.apply()
    @ancillary_layer(
        sources={
            "natural_earth": {
                "category": "physical",
                "name": "coastline",
                "attribute": "NAME_LONG",
                "label": "NAME_LONG",
            },
        },
        line=True,
        default_transform_first=True,
    )
    def coastlines(self, *args, **kwargs):
        """Add country boundary polygons from Natural Earth.

        Parameters
        ----------
        resolution: (str, optional)
            One of "low", "medium" or "high", or a named resolution from the
            Natrual Earth dataset.
        transform_first: (bool, optional)
            If True, reproject geometries before plotting for better performance.
            If False, let cartopy handle reprojection. Default is True for coastlines.
        """

    @schema.borders.apply()
    @ancillary_layer(
        sources={
            "natural_earth": {
                "category": "cultural",
                "name": "admin_0_boundary_lines_land",
                "attribute": "NAME_LONG",
                "label": "NAME_LONG",
            },
            "gisco": {
                "geometry_type": "lines",
                "attribute": "NAME_EN",
                "label": "CNTR",
            },
        },
        line=True,
        default_transform_first=True,
    )
    def borders(self, *args, **kwargs):
        """Add country boundary lines from Natural Earth or GISCO.

        Parameters
        ----------
        source: (str, optional)
            Data source to use. Valid options: "natural_earth" (default) or "gisco".
        resolution: (str, optional)
            One of "low", "medium" or "high", or a named resolution from the
            data source. For GISCO, also accepts explicit resolutions like
            "01M", "03M", "10M", "20M", "60M".
        transform_first: (bool, optional)
            If True, reproject geometries before plotting for better performance.
            If False, let cartopy handle reprojection. Default is True for borders.
        """

    @schema.unit_boundaries.apply()
    @ancillary_layer(
        sources={
            "natural_earth": {
                "category": "cultural",
                "name": {
                    "10m": "admin_0_boundary_lines_map_units",
                    "50m": "admin_0_boundary_map_units",
                },
                "attribute": "NAME_LONG",
                "label": "NAME_LONG",
            },
        },
        min_resolution="medium",
        line=True,
        default_transform_first=True,
    )
    def unit_boundaries(self, *args, **kwargs):
        """Add country boundary polygons from Natural Earth.

        Parameters
        ----------
        resolution: (str, optional)
            One of "low", "medium" or "high", or a named resolution from the
            Natrual Earth dataset.
        transform_first: (bool, optional)
            If True, reproject geometries before plotting for better performance.
            If False, let cartopy handle reprojection. Default is True for coastlines.
        """

    @schema.disputed_boundaries.apply()
    @ancillary_layer(
        sources={
            "natural_earth": {
                "category": "cultural",
                "name": {
                    "10m": "admin_0_disputed_areas",
                    "50m": "admin_0_breakaway_disputed_areas",
                },
                "attribute": "NAME_LONG",
                "label": "NAME_LONG",
            },
        },
        min_resolution="medium",
        line=True,
        default_transform_first=True,
    )
    def disputed_boundaries(self, *args, **kwargs):
        """Add country boundary polygons from Natural Earth.

        Parameters
        ----------
        resolution: (str, optional)
            One of "low", "medium" or "high", or a named resolution from the
            Natrual Earth dataset.
        transform_first: (bool, optional)
            If True, reproject geometries before plotting for better performance.
            If False, let cartopy handle reprojection. Default is True for coastlines.
        """

    @schema.administrative_areas.apply()
    @ancillary_layer(
        sources={
            "natural_earth": {
                "category": "cultural",
                "name": "admin_1_states_provinces",
                "attribute": "name",
                "label": "name",
            },
        },
        line=True,
        default_transform_first=True,
    )
    def administrative_areas(self, *args, **kwargs):
        """Add country boundary polygons from Natural Earth.

        Parameters
        ----------
        resolution: (str, optional)
            One of "low", "medium" or "high", or a named resolution from the
            Natrual Earth dataset.
        transform_first: (bool, optional)
            If True, reproject geometries before plotting for better performance.
            If False, let cartopy handle reprojection. Default is True for coastlines.
        """

    @schema.countries.apply()
    @ancillary_layer(
        sources={
            "natural_earth": {
                "category": "cultural",
                "name": "admin_0_countries",
                "attribute": "NAME_LONG",
                "label": "ISO_A2_EH",
            },
            "gisco": {
                "geometry_type": "polygons",
                "attribute": "NAME_EN",
                "label": "CNTR",
            },
        },
        default_transform_first=True,
    )
    def countries(self, *args, **kwargs):
        """Add country boundary polygons from Natural Earth or GISCO.

        Parameters
        ----------
        source: (str, optional)
            Data source to use. Valid options: "natural_earth" (default) or "gisco".
        resolution: (str, optional)
            One of "low", "medium" or "high", or a named resolution from the
            data source. For GISCO, also accepts explicit resolutions like
            "01M", "03M", "10M", "20M", "60M".
        transform_first: (bool, optional)
            If True, reproject geometries before plotting for better performance.
            If False, let cartopy handle reprojection. Default is True for countries.
        """

    def nuts_regions(
        self,
        level,
        *args,
        resolution=None,
        geometry_type="polygons",
        year=2024,
        include=None,
        exclude=None,
        labels=False,
        special_styles=None,
        adjust_labels=False,
        transform_first=True,
        **kwargs,
    ):
        """Add NUTS (Nomenclature of Territorial Units for Statistics) regions from GISCO.

        Please see https://ec.europa.eu/eurostat/web/nuts for more information.

        Parameters
        ----------
        level : int
            The NUTS level (0, 1, 2, or 3).
        resolution : str, optional
            One of "low", "medium" or "high", or a named resolution from GISCO.
            Also accepts explicit resolutions like "01M", "03M", "10M", "20M", "60M".
            Default uses the map's natural_earth_resolution setting.
        geometry_type : str, optional
            The type of geometry to retrieve. Must be one of 'polygons', 'lines', or 'points'.
            Default is 'lines'.
        year : int, optional
            The year of the NUTS data to retrieve. Default is 2024 (latest available).
            Available years: 2024, 2021, 2016, 2013, 2010, 2006, 2003.
        include : str or list of str, optional
            NUTS region names or IDs to include. If None, all regions are included.
        exclude : str or list of str, optional
            NUTS region names or IDs to exclude. If None, no regions are excluded.
        labels : bool or str, optional
            Whether to add labels to the regions. If True, uses NUTS_ID. If a string,
            uses that attribute for labels. Default is False.
        special_styles : list of dict, optional
            List of dictionaries with 'key', 'values', and 'kwargs' to apply special
            styles to specific regions.
        adjust_labels : bool, optional
            Whether to adjust label positions to avoid overlap. Default is False.
        transform_first : bool, optional
            If True, reproject geometries before plotting for better performance.
            If False, let cartopy handle reprojection. Default is True.
        **kwargs
            Additional keyword arguments to pass to the add_feature method.
        """
        from earthkit.plots.geo import gisco

        # Set default resolution
        if resolution is None:
            resolution = self.natural_earth_resolution

        # Handle color parameter for lines
        if "color" in kwargs:
            kwargs["edgecolor"] = kwargs.pop("color")

        # Set default facecolor to none for lines
        if geometry_type == "lines" and "facecolor" not in kwargs:
            kwargs["facecolor"] = "none"

        # Load NUTS regions data
        records_list, attribute_key, label_key = gisco.load_nuts_layer(
            level, resolution, geometry_type, year
        )

        # Add attribution
        self.figure.add_attribution(
            "© EuroGeographics for the administrative boundaries"
        )

        # Common processing (filter records, add labels, add geometries)
        filtered_records = []
        special_records = []

        if special_styles is not None:
            for record in records_list:
                for style in special_styles:
                    if record.attributes.get(style["key"], None) in style["values"]:
                        special_records.append([record, style["kwargs"]])
                    else:
                        filtered_records.append(record)
        else:
            filtered_records = records_list

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
                for record in records_list
                if (
                    (
                        include is None
                        or record.attributes.get(attribute_key) in include
                        or record.attributes.get(label_key) in include
                    )
                    and (
                        exclude is None
                        or (
                            record.attributes.get(attribute_key) not in exclude
                            and record.attributes.get(label_key) not in exclude
                        )
                    )
                )
            ]

        if labels:
            if not isinstance(labels, str):
                labels = label_key
            # GISCO may not have label positions, use centroid
            self._add_polygon_labels(
                filtered_records,
                x_key=None,  # Will compute from geometry
                y_key=None,
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
        if transform_first and target_crs != src_crs:
            from earthkit.plots.geo.geometry import reproject_geometries

            # Reproject geometries before adding to map for better performance
            geometries = reproject_geometries(geometries, src_crs, target_crs)
            feature_crs = target_crs
        else:
            # Let cartopy handle reprojection
            feature_crs = src_crs

        # Add optimized features
        feature = cfeature.ShapelyFeature(geometries, feature_crs)
        result = self.ax.add_feature(feature, *args, **kwargs)

        if special_styles is not None:
            for record, style in special_records:
                geom = record.geometry
                if not geom.is_empty:
                    feature = cfeature.ShapelyFeature([geom], self.crs)
                    self.ax.add_feature(feature, *args, **{**kwargs, **style})

        return result

    @schema.land.apply()
    @ancillary_layer(
        sources={
            "natural_earth": {
                "category": "physical",
                "name": "land",
                "attribute": "NAME_LONG",
                "label": "NAME_LONG",
            },
        },
        default_transform_first=True,
    )
    def land(self, *args, **kwargs):
        """Add country boundary polygons from Natural Earth.

        Parameters
        ----------
        resolution: (str, optional)
            One of "low", "medium" or "high", or a named resolution from the
            Natrual Earth dataset.
        transform_first: (bool, optional)
            If True, reproject geometries before plotting for better performance.
            If False, let cartopy handle reprojection. Default is True for coastlines.
        """

    @schema.ocean.apply()
    @ancillary_layer(
        sources={
            "natural_earth": {
                "category": "physical",
                "name": "ocean",
                "attribute": "NAME_LONG",
                "label": "NAME_LONG",
            },
        },
    )
    def ocean(self, *args, **kwargs):
        """Add country boundary polygons from Natural Earth.

        Parameters
        ----------
        resolution: (str, optional)
            One of "low", "medium" or "high", or a named resolution from the
            Natrual Earth dataset.
        transform_first: (bool, optional)
            If True, reproject geometries before plotting for better performance.
            If False, let cartopy handle reprojection. Default is True for coastlines.
        """

    @schema.urban_areas.apply()
    @ancillary_layer(
        sources={
            "natural_earth": {
                "category": "cultural",
                "name": "urban_areas",
                "attribute": "NAME_LONG",
                "label": "NAME_LONG",
            },
        },
        default_transform_first=True,
    )
    def urban_areas(self, *args, **kwargs):
        """Add country boundary polygons from Natural Earth.

        Parameters
        ----------
        resolution: (str, optional)
            One of "low", "medium" or "high", or a named resolution from the
            Natrual Earth dataset.
        transform_first: (bool, optional)
            If True, reproject geometries before plotting for better performance.
            If False, let cartopy handle reprojection. Default is True for coastlines.
        """

    @schema.countries.apply()
    @ancillary_layer(
        sources={
            "natural_earth": {
                "category": "cultural",
                "name": "admin_0_map_units",
                "attribute": "NAME_LONG",
                "label": "ADM0_TLC",
            },
        },
        default_transform_first=True,
    )
    def map_units(self, *args, **kwargs):
        """Add country boundary polygons from Natural Earth.

        Parameters
        ----------
        resolution: (str, optional)
            One of "low", "medium" or "high", or a named resolution from the
            Natrual Earth dataset.
        transform_first: (bool, optional)
            If True, reproject geometries before plotting for better performance.
            If False, let cartopy handle reprojection. Default is True for coastlines.
        """

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

    @schema.legend.apply()
    def legend(self, style=None, location=None, **kwargs):
        """
        Add a legend to the Subplot.

        Parameters
        ----------
        style : Style, optional
            The Style to use for the legend. If None (default), a legend is
            created for each Layer with a unique Style. If a single Style is
            provided, a single legend is created based on that Style.
        location : str or tuple, optional
            The location of the legend(s). Must be a valid matplotlib location
            (see :func:`matplotlib.pyplot.legend`).
        **kwargs
            Additional keyword arguments to pass to :func:`matplotlib.pyplot.legend`.
        """
        from earthkit.plots.components.layers import Layer
        from earthkit.plots.sources import get_source

        legends = []
        if style is not None:
            dummy = [[1, 2], [3, 4]]
            mappable = self.contourf(x=dummy, y=dummy, z=dummy, style=style)
            # Create a dummy source for legend creation
            dummy_source = get_source(dummy, x=dummy, y=dummy, z=dummy)
            layer = Layer(dummy_source, mappable, self, style)
            legend = layer.style.legend(layer, label=kwargs.pop("label", ""), **kwargs)
            legends.append(legend)
        else:
            for i, layer in enumerate(self.distinct_legend_layers):
                if isinstance(location, (list, tuple)):
                    loc = location[i]
                else:
                    loc = location
                if layer.style is not None:
                    legend = layer.style.legend(layer, location=loc, **kwargs)
                legends.append(legend)
        return legends

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
            kwargs["xlocs"] = step_range([-180, 180], xstep, xref)
        if ystep is not None:
            kwargs["ylocs"] = step_range([-90, 90], ystep, yref)
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
