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

from earthkit.plots.components.extractors import configure_style
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

    def natural_earth_layer(
        category,
        name,
        default_attribute="NAME_LONG",
        default_label="NAME_LONG",
        max_resolution="high",
        min_resolution="low",
        line=False,
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
                **kwargs,
            ):
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

                # Add optimized features
                feature = cfeature.ShapelyFeature(geometries, ccrs.PlateCarree())
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
    @natural_earth_layer("physical", "coastline", line=True)
    def coastlines(self, *args, **kwargs):
        """Add country boundary polygons from Natural Earth.

        Parameters
        ----------
        resolution: (str, optional)
            One of "low", "medium" or "high", or a named resolution from the
            Natrual Earth dataset.
        """

    @schema.borders.apply()
    @natural_earth_layer("cultural", "admin_0_boundary_lines_land", line=True)
    def borders(self, *args, **kwargs):
        """Add country boundary polygons from Natural Earth.

        Parameters
        ----------
        resolution: (str, optional)
            One of "low", "medium" or "high", or a named resolution from the
            Natrual Earth dataset.
        """

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

    # @schema.choropleth.apply()
    def choropleth(
        self,
        data,
        *args,
        z=None,
        style=None,
        units=None,
        labels=False,
        exclude_nan_labels=True,
        auto_style=True,
        metadata=None,
        **kwargs,
    ):
        """
        Create a choropleth map from GeoDataFrame.

        A choropleth map displays regions (polygons) colored according to
        data values. Commonly used for visualizing statistics by geographic
        region (e.g., population by country, temperature by state).

        Parameters
        ----------
        data : geopandas.GeoDataFrame or GeometrySource
            The data to plot. Can be:
            - GeoDataFrame with geometry column and data columns
            - GeometrySource object created from GeoDataFrame
        z : str, optional
            Name of the column containing data values for coloring.
            If None, auto-detects first numeric column.
        style : Style, optional
            Style object for customizing appearance (colors, colormap, etc.)
        units : str, optional
            Target units for data values (e.g., "celsius", "kilometers")
        labels : bool or str, optional
            Label configuration:
            - False (default): No labels
            - True: Use data values as labels
            - str without {}: Column name to use for labels (e.g., "country_name")
            - str with {}: Template string with Python format specifiers
              Supports numeric formatting: "{temperature:.1f}°C", "{population:,.0f}"
              Multi-column templates: "{name}: {value} units"
              Metadata access: "{value:.1f} {units}", "{long_name}"
              Unit formatting: "{units}" (default: ~E format) or "{units:E}" (E=LaTeX), "{units:R}" (raw)
        exclude_nan_labels : bool, optional
            Whether to exclude labels for geometries where the z-value is NaN.
            Default is True (NaN values are not labeled).
        auto_style : bool, optional
            Whether to automatically generate style. Default is True.
        metadata : dict, optional
            Additional metadata for the data source
        **kwargs
            Additional keyword arguments:
            - cmap : str - Colormap name (default: "viridis")
            - vmin, vmax : float - Color scale limits
            - edgecolor : color - Edge color for geometries (default: "black")
            - linewidth : float - Edge line width (default: 0.5)
            - alpha : float - Transparency (0-1)
            - colorbar : bool - Whether to show colorbar (default: True)
            - adjust_labels : bool - Whether to adjust label positions to avoid overlap (default: False)

        Returns
        -------
        matplotlib collection
            The matplotlib collection representing the choropleth

        Examples
        --------
        >>> import geopandas as gpd
        >>> from earthkit.plots import Map
        >>>
        >>> # Basic choropleth with auto-detected data column
        >>> gdf = gpd.read_file("countries.shp")
        >>> map = Map(domain="global")
        >>> map.choropleth(gdf)
        >>> map.show()
        >>>
        >>> # Specify data column and colormap
        >>> map.choropleth(gdf, z="population", cmap="YlOrRd")
        >>>
        >>> # With labels using data values (labels=True)
        >>> map.choropleth(gdf, z="gdp", labels=True)
        >>>
        >>> # With labels using a specific column
        >>> map.choropleth(gdf, z="population", labels="country_name")
        >>>
        >>> # With labels using template strings
        >>> map.choropleth(gdf, z="storms", labels="{name}: {storms} storms")
        >>>
        >>> # With numeric formatting in labels
        >>> map.choropleth(gdf, z="temp", labels="{region}: {temp:.1f}°C")
        >>> map.choropleth(gdf, z="population", labels="{name}\n{population:,.0f}")
        >>>
        >>> # With metadata in labels (e.g., units from source)
        >>> map.choropleth(
        ...     gdf, z="temperature", labels="{name}: {temperature:.1f} {units}"
        ... )
        >>> map.choropleth(gdf, z="value", labels="{long_name}\n{value:.2f}")
        >>>
        >>> # With formatted units (LaTeX rendering)
        >>> map.choropleth(
        ...     gdf, z="wind_speed", labels="{name}\n{wind_speed:.1f} {units:E}"
        ... )
        >>> # Output: "Region A\n15.7 $m \\cdot s^{-1}$"
        >>>
        >>> # With unit conversion
        >>> map.choropleth(gdf, z="temperature", units="celsius", cmap="RdBu_r")
        >>>
        >>> # With custom levels and style
        >>> from earthkit.plots import Style
        >>> style = Style(levels=[0, 10, 20, 30, 40], cmap="viridis")
        >>> map.choropleth(gdf, z="value", style=style)
        """
        import cartopy.crs as ccrs
        from matplotlib.cm import ScalarMappable

        from earthkit.plots.components.layers import Layer
        from earthkit.plots.sources import get_source
        from earthkit.plots.sources.context import PlotContext
        from earthkit.plots.sources.geometry import GeometrySource

        if style is not None:
            units = units or style.units

        # Convert to GeometrySource if not already
        if not isinstance(data, GeometrySource):
            source = get_source(
                data,
                z=z,  # z parameter specifies the data column for geometry
                context=PlotContext.GEOGRAPHIC_GEOMETRY,
                units=units,
                metadata=metadata,
            )
        else:
            source = data

        # Get geometries and data values
        geometries = source.geometries
        data_values = source.values

        # Get CRS from source (or default to PlateCarree)
        source_crs = source.crs
        if source_crs is None:
            source_crs = ccrs.PlateCarree()

        # Extract kwargs for matplotlib
        style = configure_style(
            "add_geometries", style, source, units, auto_style, kwargs
        )
        style_kwargs = style.to_add_geometries_kwargs(data_values)

        # Prepare colors based on data values
        if data_values is not None and auto_style:
            # Store norm and cmap for colorbar
            scalar_mappable = ScalarMappable(
                norm=style_kwargs["norm"], cmap=style_kwargs["cmap"]
            )
            scalar_mappable.set_array(data_values)
        else:
            # No data values or no auto_style - use single color
            scalar_mappable = None

        # Render geometries
        collection = self.ax.add_geometries(
            geometries,
            crs=source_crs,
            **{**style_kwargs, **kwargs},
        )

        # Create layer for style/legend management
        layer = Layer(source, collection, self, style)
        if scalar_mappable is not None:
            # Store scalar_mappable on layer for colorbar
            layer._scalar_mappable = scalar_mappable
            layer._units = source.units
            layer._value_name = source.value_name
        self.layers.append(layer)

        # Add labels if requested
        if labels:
            label_column = labels if not isinstance(labels, bool) else source._column
            self._add_choropleth_labels(
                source, label_column, exclude_nan_labels=exclude_nan_labels, **kwargs
            )

        return collection

    def _add_choropleth_labels(
        self, source, label_column=None, exclude_nan_labels=True, **kwargs
    ):
        """
        Add labels to choropleth geometries.

        Parameters
        ----------
        source : GeometrySource
            The GeometrySource with geometries, data, and metadata
        label_column : str, optional
            Column name to use for labels, or a template string with format
            specifiers. Supports Python format specification mini-language for
            numbers and can include metadata keys. Examples:
            - "country_name" - Direct column reference
            - "{country_name}" - Template with single column
            - "{name}: {storms} storms" - Multi-column template
            - "{temperature:.1f}°C" - Numeric formatting (1 decimal place)
            - "Pop: {population:,.0f}" - Thousands separator, no decimals
            - "{value:.1f} {units}" - Include metadata with default ~E formatting
            - "{long_name}: {value:.2f}" - Include metadata long_name
            - "{value:.1f} {units:E}" - Format units explicitly (E=LaTeX, R=raw)
            - "{value:.1f} {units:R}" - Raw units (no formatting)
        exclude_nan_labels : bool, optional
            Whether to exclude labels for geometries where the z-value is NaN.
            Default is True.
        **kwargs
            Additional keyword arguments (e.g., adjust_labels)
        """
        from types import SimpleNamespace

        import numpy as np

        gdf = source.data
        data_values = source.values

        # Check if label_column is a template string (contains curly braces)
        is_template = label_column is not None and "{" in str(label_column)

        # Determine label column or template
        if label_column is None:
            # Auto-detect: look for columns with 'name' in them
            name_cols = [col for col in gdf.columns if "name" in col.lower()]
            label_column = name_cols[0] if name_cols else None

        if label_column is None:
            # No suitable label column found
            return

        # Build metadata dict from source
        # Common metadata keys users might want to access
        metadata_keys = ["units", "long_name", "standard_name", "variable_name", "name"]
        source_metadata = {}
        for key in metadata_keys:
            value = source.metadata(key)
            if value is not None:
                source_metadata[key] = value

        # Parse template to detect units format spec
        units_format_spec = None
        has_units_placeholder = False
        template_for_formatting = label_column
        if is_template and "units" in source_metadata:
            import re

            # Check if {units} appears anywhere in the template
            has_units_placeholder = (
                re.search(r"\{units(?::[^}]+)?\}", label_column) is not None
            )

            # Look for {units:format_spec} pattern
            units_match = re.search(r"\{units:([^}]+)\}", label_column)
            if units_match:
                units_format_spec = units_match.group(1)
                # Remove the format spec from the template since we'll pre-format units
                template_for_formatting = re.sub(
                    r"\{units:[^}]+\}", "{units}", label_column
                )
            elif has_units_placeholder:
                # {units} without format spec - use default format
                units_format_spec = "~E"

        # Create records-like structure for _add_polygon_labels
        records = []
        for idx, row in gdf.iterrows():
            # Skip this geometry if exclude_nan_labels is True and z-value is NaN
            if exclude_nan_labels and data_values is not None:
                if np.isnan(data_values[idx]):
                    continue

            record = SimpleNamespace()
            record.geometry = row.geometry

            if is_template:
                # Use template string with row data and metadata
                # Create a formatter dict combining row data and metadata
                formatter = {col: row[col] for col in gdf.columns if col != "geometry"}
                # Add metadata to formatter (metadata takes precedence for conflicts)
                formatter.update(source_metadata)

                # Format units if units placeholder is present
                if has_units_placeholder and "units" in formatter:
                    from earthkit.plots.metadata import units as metadata_units

                    formatter["units"] = metadata_units.format_units(
                        formatter["units"], format=units_format_spec
                    )

                try:
                    label_text = template_for_formatting.format(**formatter)
                except KeyError as e:
                    import warnings

                    warnings.warn(
                        f"Column/metadata key {e} not found for label template. "
                        f"Available columns: {list(gdf.columns)} "
                        f"Available metadata: {list(source_metadata.keys())}"
                    )
                    label_text = str(row.get(label_column, ""))

                # Store the formatted label in a special key
                record.attributes = {"__label__": label_text}
                label_key_to_use = "__label__"
            else:
                # Use direct column value
                record.attributes = {label_column: row[label_column]}
                label_key_to_use = label_column

            records.append(record)

        # Use existing _add_polygon_labels infrastructure
        self._add_polygon_labels(
            records,
            label_key=label_key_to_use,
            adjust_labels=kwargs.get("adjust_labels", False),
        )

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
