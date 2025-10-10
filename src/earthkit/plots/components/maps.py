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
        coordinates, or a Domain object. This is used to set the extent and
        projection of the map.
    crs : cartopy.crs.CRS, optional
        The CRS of the map. If not provided, it will be inferred from the
        domain or set to PlateCarree.
    **kwargs
        Additional keyword arguments to pass to the matplotlib Axes object.
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
        """The CRS of the map."""
        if self._crs is not None:
            return self._crs
        elif self.domain is not None:
            return self.domain.bbox.crs
        elif self._crs is None:
            return ccrs.PlateCarree()

    @property
    def crs_name(self):
        """The human-readable name of the CRS of the map."""
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
    def fig(self):
        """The matplotlib Figure object to which the subplot belongs."""
        return self.figure.fig

    @property
    def ax(self):
        """The matplotlib Axes object of the subplot."""
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
            Additional keyword arguments to pass to `matplotlib.pyplot.scatter`.
        """
        popped_kwargs = []
        for key in ["style", "levels", "units", "colors"]:
            if key in kwargs:
                popped_kwargs.append(key)
                kwargs.pop(key)
        return self.scatter(*args, **kwargs)

    def gridpoints(self, *args, **kwargs):
        import warnings

        warnings.warn(
            "gridpoints is deprecated and will be removed in a future release. "
            "Please use grid_points instead."
        )
        return self.grid_points(*args, **kwargs)

    def labels(self, data=None, label=None, x=None, y=None, **kwargs):
        source = get_source(data=data, x=x, y=y)
        labels = SourceFormatter(source).format(label)
        crs = source.crs or ccrs.PlateCarree()
        for label, x, y in zip(labels, source.x_values, source.y_values):
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
        **kwargs
            Additional keyword arguments to pass to `matplotlib.pyplot.scatter`.
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
        def decorator(method):
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
