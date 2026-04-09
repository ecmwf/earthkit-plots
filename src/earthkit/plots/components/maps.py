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

from earthkit.plots.components._chainable import chainable_method
from earthkit.plots.components.subplots import Subplot
from earthkit.plots.geography import (
    coordinate_reference_systems,
    domains,
    natural_earth,
)
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
        coordinates, or a :class:`earthkit.plots.geography.domains.Domain` object. This is used to set the extent and
        projection of the map.
    crs : cartopy.crs.CRS, optional
        The CRS of the map. If not provided, it will be inferred from the
        domain. See
        https://cartopy.readthedocs.io/stable/reference/projections.html#cartopy-projections
        for a list of available CRSs.
    **kwargs
        Additional keyword arguments to pass to the :class:`matplotlib.axes.Axes` object.
    """

    def __init__(self, *args, domain=None, crs=None, ax=None, **kwargs):
        super().__init__(*args, ax=ax, **kwargs)
        if isinstance(crs, str):
            crs = coordinate_reference_systems.parse_crs(crs)
        # When an existing GeoAxes is supplied, read its projection back so
        # self.crs is consistent and _plot_kwargs() returns the right transform.
        if ax is not None and crs is None and hasattr(ax, "projection"):
            crs = ax.projection
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

    def grid_cells(
        self,
        *args,
        x=None,
        y=None,
        z=None,
        style=None,
        every=None,
        auto_style=False,
        resample=None,
        grid="auto",
        **kwargs,
    ):
        """
        Plot data as grid cells using the specialised nnshow backends.

        For HEALPix and octahedral reduced Gaussian grids the fast pixel-
        sampling ``nnshow`` backends are used automatically.  For other grid
        types, plain pcolormesh rendering is used.

        Parameters
        ----------
        data : xarray.DataArray or earthkit.data.core.Base, optional
            The data to plot.
        x, y, z : str, array-like, or None, optional
            Explicit coordinates / values.
        style : earthkit.plots.styles.Style, optional
            Style to apply.
        units : str, optional
            Target units for value conversion (e.g. ``"celsius"``). See
            :doc:`/examples/examples/introduction/08-unit-conversion` for
            examples.
        grid : str or GridSpec, optional
            Grid specification to use for rendering.  Pass ``"auto"`` (the
            default) to detect the grid type from the data metadata.  Pass a
            :class:`~earthkit.plots.sources.gridspec.GridSpec` (or compatible
            object with a ``.name`` attribute) to override the detected grid —
            useful when the source metadata is absent or incorrect.
        **kwargs
            Additional keyword arguments forwarded to the underlying plot method.
        """
        if resample is not None:
            raise ValueError(
                "grid_cells does not support the 'resample' argument. "
                "Use pcolormesh with resample=Bilinear(...) or resample=NearestNeighbour(...) instead."
            )
        from earthkit.plots.components._pipeline import extract_plottables_2D

        return extract_plottables_2D(
            subplot=self,
            method_name="pcolormesh",
            args=args,
            x=x,
            y=y,
            z=z,
            style=style,
            every=every,
            auto_style=auto_style,
            extract_domain=True,
            use_nn_sampling=True,
            grid=grid,
            **kwargs,
        )

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
            Additional keyword arguments passed to
            :meth:`matplotlib.axes.Axes.scatter`.
            See the `matplotlib scatter documentation
            <https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.scatter.html>`_
            for the full list of accepted arguments.
        """
        if "resample" in kwargs:
            raise ValueError("The 'resample' argument is not supported for grid_points.")
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
            Additional keyword arguments passed to
            :meth:`matplotlib.axes.Axes.scatter`.
        """
        import warnings

        warnings.warn(
            "gridpoints is deprecated and will be removed in earthkit-plots 0.6. Please use grid_points instead."
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
            Additional keyword arguments passed to
            :meth:`matplotlib.axes.Axes.annotate`.
        """
        source = get_source(data=data, x=x, y=y)
        labels = SourceFormatter(source).format(label)
        crs = source.crs or ccrs.PlateCarree()
        for label, x, y in zip(labels, source.x.values, source.y.values):
            self.ax.annotate(label, (x, y), transform=crs, **kwargs)

    @schema.point_cloud.apply()
    def point_cloud(self, *args, **kwargs):
        """
        Plot data values as a coloured point cloud on the map.

        Each data point is rendered as a scatter point coloured by its value.
        Suitable for sparse or unstructured observation data.

        Parameters
        ----------
        data : xarray.DataArray or earthkit.data.core.Base, optional
            The data to plot.
        x : str, optional
            The name of the x-coordinate variable in the data source.
        y : str, optional
            The name of the y-coordinate variable in the data source.
        units : str, optional
            Target units for value conversion (e.g. ``"celsius"``). See
            :doc:`/examples/examples/introduction/08-unit-conversion` for
            examples.
        **kwargs
            Additional keyword arguments passed to
            :meth:`matplotlib.axes.Axes.scatter`.
            See the `matplotlib scatter documentation
            <https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.scatter.html>`_
            for the full list of accepted arguments.
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
                _transform_first = default_transform_first if transform_first is None else transform_first

                if source not in sources:
                    raise ValueError(
                        f"source='{source}' is not supported for this method. Valid sources are: {list(sources.keys())}"
                    )

                source_config = sources[source]

                # Set default resolution
                if resolution is None:
                    resolution = self.natural_earth_resolution

                # Load data using source-specific loader
                if source == "gisco":
                    from earthkit.plots.geography import gisco

                    records_list, attribute_key, label_key = gisco.load_layer(source_config, resolution)
                    self.figure.attribution("© EuroGeographics for the administrative boundaries")

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

                # Build a cache key from everything that determines the geometry set.
                # kwargs is excluded — only the geometry/projection inputs matter.
                # The extent is not part of the key because reproject_geometries
                # operates on the full global geometry; clipping to the axes extent
                # happens at render time by matplotlib/cartopy.
                if self.domain is not None:
                    _llbbox = self.domain.bbox.to_latlon_bbox
                    _domain_key = (
                        round(_llbbox.x_min, 4),
                        round(_llbbox.x_max, 4),
                        round(_llbbox.y_min, 4),
                        round(_llbbox.y_max, 4),
                    )
                else:
                    _domain_key = None
                cache_key = (
                    method.__name__,
                    source,
                    resolution,
                    tuple(sorted(include)) if include is not None else None,
                    tuple(sorted(exclude)) if exclude is not None else None,
                    str(special_styles),
                    _transform_first,
                    tuple(sorted(self.crs.proj4_params.items())),
                    _domain_key,
                )
                cached = getattr(self.figure, "_ancillary_cache", {}).get(cache_key)

                if cached is not None:
                    feature, special_features = cached
                    self.ax.add_feature(feature, *args, **kwargs)
                    for sf, sf_kwargs in special_features:
                        self.ax.add_feature(sf, *args, **{**kwargs, **sf_kwargs})
                    return None

                filtered_records = []
                special_records = []

                if special_styles is not None:
                    for record in records_list:
                        matched = False
                        for style in special_styles:
                            if record.attributes.get(style["key"], None) in style["values"]:
                                special_records.append([record, style["kwargs"]])
                                matched = True
                                break
                        if not matched:
                            filtered_records.append(record)
                else:
                    filtered_records = records_list

                if include is not None or exclude is not None:
                    exclude = [exclude] if not (isinstance(exclude, (list, tuple)) or exclude is None) else exclude
                    include = [include] if not (isinstance(include, (list, tuple)) or include is None) else include

                    filtered_records = [
                        record
                        for record in records_list
                        if (
                            (include is None or record.attributes.get(attribute_key) in include)
                            and (exclude is None or record.attributes.get(attribute_key) not in exclude)
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

                # Clip geometries to the domain extent (in PlateCarree) before
                # reprojecting. Natural Earth shapefiles are global; for small
                # domains this can eliminate the vast majority of vertices and
                # dramatically reduces both reprojection and rasterisation cost.
                clip_box = None
                if _domain_key is not None:
                    from shapely.geometry import box as shapely_box

                    pad = 5.0  # degrees — avoids excluding features on the boundary
                    clip_box = shapely_box(
                        max(_llbbox.x_min - pad, -180),
                        max(_llbbox.y_min - pad, -90),
                        min(_llbbox.x_max + pad, 180),
                        min(_llbbox.y_max + pad, 90),
                    )

                geometries = []
                for record in filtered_records:
                    geom = record.geometry

                    if not geom.is_empty:  # Only keep visible parts
                        # If a clip box is defined, skip geometries that don't
                        # intersect the domain at all — but keep the full geometry
                        # intact to avoid breaking polar or antimeridian-spanning
                        # features.
                        if clip_box is not None and not geom.intersects(clip_box):
                            continue
                        geometries.append(geom)

                # Determine source and target CRS for features.
                # Natural Earth shapefiles are always in PlateCarree(-180..180).
                src_crs = ccrs.PlateCarree()
                target_crs = self.crs

                # Apply transform_first optimization if requested and needed.
                # crs_equal defaults to comparing against PlateCarree, which is
                # exactly the Natural Earth source CRS.
                if _transform_first and not coordinate_reference_systems.crs_equal(target_crs, match_type_only=True):
                    from earthkit.plots.geography.geometry import reproject_geometries

                    # Reproject geometries before adding to map for better performance
                    geometries = reproject_geometries(geometries, src_crs, target_crs)
                    feature_crs = target_crs
                else:
                    # Let cartopy handle reprojection (needed for proper line interpolation)
                    feature_crs = src_crs

                # Build and cache the ShapelyFeature so subsequent subplots with
                # the same domain/CRS can skip geometry loading and reprojection.
                feature = cfeature.ShapelyFeature(geometries, feature_crs)
                special_features = []
                if special_styles is not None:
                    for record, sf_kwargs in special_records:
                        geom = record.geometry
                        if clip_box is not None:
                            geom = geom.intersection(clip_box)
                        if _transform_first and not coordinate_reference_systems.crs_equal(
                            target_crs, match_type_only=True
                        ):
                            from earthkit.plots.geography.geometry import (
                                reproject_geometries,
                            )

                            reprojected = reproject_geometries([geom], src_crs, target_crs)
                            if not reprojected:
                                continue
                            geom = reprojected[0]
                        if not geom.is_empty:
                            special_features.append((
                                cfeature.ShapelyFeature([geom], feature_crs),
                                sf_kwargs,
                            ))

                if hasattr(self.figure, "_ancillary_cache"):
                    self.figure._ancillary_cache[cache_key] = (
                        feature,
                        special_features,
                    )

                self.ax.add_feature(feature, *args, **kwargs)
                for sf, sf_kwargs in special_features:
                    self.ax.add_feature(sf, *args, **{**kwargs, **sf_kwargs})
                return None

            return wrapper

        return decorator

    @chainable_method
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
        """Add coastlines from Natural Earth.

        Parameters
        ----------
        resolution : str, optional
            One of ``"low"``, ``"medium"`` or ``"high"``, or a named resolution
            from the Natural Earth dataset.
        transform_first : bool, optional
            If ``True``, reproject geometries before plotting for better
            performance. If ``False``, let cartopy handle reprojection.
            Default is ``True``.
        **kwargs
            Additional keyword arguments passed to cartopy's
            ``add_feature`` method.
        """

    @chainable_method
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
        source : str, optional
            Data source to use. Valid options: ``"natural_earth"`` (default)
            or ``"gisco"``.
        resolution : str, optional
            One of ``"low"``, ``"medium"`` or ``"high"``, or a named resolution
            from the data source. For GISCO, also accepts explicit resolutions
            like ``"01M"``, ``"03M"``, ``"10M"``, ``"20M"``, ``"60M"``.
        transform_first : bool, optional
            If ``True``, reproject geometries before plotting for better
            performance. If ``False``, let cartopy handle reprojection.
            Default is ``True``.
        **kwargs
            Additional keyword arguments passed to cartopy's
            ``add_feature`` method.
        """

    @chainable_method
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
        """Add map-unit boundary lines from Natural Earth.

        These are boundaries between territories that share a country code
        (e.g. overseas territories and metropolitan areas).

        Parameters
        ----------
        resolution : str, optional
            One of ``"low"``, ``"medium"`` or ``"high"``, or a named resolution
            from the Natural Earth dataset.
        transform_first : bool, optional
            If ``True``, reproject geometries before plotting for better
            performance. If ``False``, let cartopy handle reprojection.
            Default is ``True``.
        **kwargs
            Additional keyword arguments passed to cartopy's
            ``add_feature`` method.
        """

    @chainable_method
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
        """Add disputed and breakaway territory boundary lines from Natural Earth.

        Parameters
        ----------
        resolution : str, optional
            One of ``"low"``, ``"medium"`` or ``"high"``, or a named resolution
            from the Natural Earth dataset.
        transform_first : bool, optional
            If ``True``, reproject geometries before plotting for better
            performance. If ``False``, let cartopy handle reprojection.
            Default is ``True``.
        **kwargs
            Additional keyword arguments passed to cartopy's
            ``add_feature`` method.
        """

    @chainable_method
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
        """Add administrative (sub-national) boundary lines from Natural Earth.

        Parameters
        ----------
        resolution : str, optional
            One of ``"low"``, ``"medium"`` or ``"high"``, or a named resolution
            from the Natural Earth dataset.
        transform_first : bool, optional
            If ``True``, reproject geometries before plotting for better
            performance. If ``False``, let cartopy handle reprojection.
            Default is ``True``.
        **kwargs
            Additional keyword arguments passed to cartopy's
            ``add_feature`` method.
        """

    @chainable_method
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
        source : str, optional
            Data source to use. Valid options: ``"natural_earth"`` (default)
            or ``"gisco"``.
        resolution : str, optional
            One of ``"low"``, ``"medium"`` or ``"high"``, or a named resolution
            from the data source. For GISCO, also accepts explicit resolutions
            like ``"01M"``, ``"03M"``, ``"10M"``, ``"20M"``, ``"60M"``.
        transform_first : bool, optional
            If ``True``, reproject geometries before plotting for better
            performance. If ``False``, let cartopy handle reprojection.
            Default is ``True``.
        **kwargs
            Additional keyword arguments passed to cartopy's
            ``add_feature`` method.
        """

    @chainable_method
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
        from earthkit.plots.geography import gisco

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
        records_list, attribute_key, label_key = gisco.load_nuts_layer(level, resolution, geometry_type, year)

        # Add attribution
        self.figure.attribution("© EuroGeographics for the administrative boundaries")

        # Common processing (filter records, add labels, add geometries)
        filtered_records = []
        special_records = []

        if special_styles is not None:
            for record in records_list:
                matched = False
                for style in special_styles:
                    if record.attributes.get(style["key"], None) in style["values"]:
                        special_records.append([record, style["kwargs"]])
                        matched = True
                        break
                if not matched:
                    filtered_records.append(record)
        else:
            filtered_records = records_list

        if include is not None or exclude is not None:
            exclude = [exclude] if not (isinstance(exclude, (list, tuple)) or exclude is None) else exclude
            include = [include] if not (isinstance(include, (list, tuple)) or include is None) else include

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

        # Determine source and target CRS for features.
        # Natural Earth shapefiles are always in PlateCarree(-180..180).
        src_crs = ccrs.PlateCarree()
        target_crs = self.crs

        # Apply transform_first optimization if requested and needed.
        # crs_equal defaults to comparing against PlateCarree, which is
        # exactly the Natural Earth source CRS.
        if transform_first and not coordinate_reference_systems.crs_equal(target_crs, match_type_only=True):
            from earthkit.plots.geography.geometry import reproject_geometries

            # Reproject geometries before adding to map for better performance
            geometries = reproject_geometries(geometries, src_crs, target_crs)
            feature_crs = target_crs
        else:
            # Let cartopy handle reprojection
            feature_crs = src_crs

        # Add optimized features
        feature = cfeature.ShapelyFeature(geometries, feature_crs)
        self.ax.add_feature(feature, *args, **kwargs)

        if special_styles is not None:
            for record, style in special_records:
                geom = record.geometry
                if not geom.is_empty:
                    feature = cfeature.ShapelyFeature([geom], self.crs)
                    self.ax.add_feature(feature, *args, **{**kwargs, **style})

    @chainable_method
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

    @chainable_method
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

    @chainable_method
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

    @chainable_method
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

    @chainable_method
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
            capital_cities_kwargs = kwargs or natural_earth.DEFAULT_CAPITAL_CITIES_KWARGS
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

    @chainable_method
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

    @chainable_method
    def add_wms(self, *args, **kwargs):
        """
        Add a WMS (Web Map Service) image to the map.

        All arguments are forwarded directly to cartopy's
        :meth:`GeoAxes.add_wms
        <cartopy.mpl.geoaxes.GeoAxes.add_wms>`.

        Parameters
        ----------
        *args
            Positional arguments passed to
            :meth:`cartopy.mpl.geoaxes.GeoAxes.add_wms`.
        **kwargs
            Keyword arguments passed to
            :meth:`cartopy.mpl.geoaxes.GeoAxes.add_wms`.
        """
        self.ax.add_wms(*args, **kwargs)

    @chainable_method
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
        self.ax.imshow(img, origin=origin, extent=extent, transform=transform)

    @chainable_method
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
        self.ax.add_geometries(shapes.geometries(), transform, *args, **kwargs)
        if labels:
            label_key = labels if isinstance(labels, str) else None
            self._add_polygon_labels(list(shapes.records()), label_key=label_key, adjust_labels=adjust_labels)

    @chainable_method
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
        Create a choropleth map from a GeoDataFrame.

        A choropleth map displays regions (polygons) colored according to
        data values. Commonly used for visualizing statistics by geographic
        region (e.g., population by country, temperature by state).

        Parameters
        ----------
        data : geopandas.GeoDataFrame
            The data to plot. Must have a geometry column and at least one
            numeric data column.
        z : str, optional
            Name of the column containing data values for coloring.
            If None, auto-detects first numeric column.
        style : Style, optional
            Style object for customizing appearance (colors, colormap, etc.)
        units : str, optional
            Target units for data values (e.g. ``"celsius"``). See
            :doc:`/examples/examples/introduction/08-unit-conversion` for
            examples.
        labels : bool or str, optional
            Label configuration:
            - False (default): No labels
            - True: Use data values as labels
            - str without {}: Column name to use for labels (e.g., "country_name")
            - str with {}: Template string with Python format specifiers
              e.g. "{name}: {value:.1f} {units}"
        exclude_nan_labels : bool, optional
            Whether to exclude labels for geometries where the z-value is NaN.
            Default is True.
        auto_style : bool, optional
            Whether to automatically generate style. Default is True.
        metadata : dict, optional
            Additional metadata for the data source.
        **kwargs
            Additional keyword arguments passed to cartopy's add_geometries,
            e.g. edgecolor, linewidth, alpha.

        Returns
        -------
        matplotlib collection
            The matplotlib collection representing the choropleth.
        """
        import cartopy.crs as ccrs
        from matplotlib.cm import ScalarMappable

        from earthkit.plots.components._style_utils import configure_style
        from earthkit.plots.components.layers import Layer
        from earthkit.plots.sources.geometry import GeometrySource

        if style is not None and hasattr(style, "units") and style.units:
            units = units or style.units

        # Convert earthkit-data objects to GeoDataFrame first
        import earthkit.data as ek_data

        if isinstance(data, ek_data.core.Base) and hasattr(data, "to_geopandas"):
            data = data.to_geopandas()

        # Convert to GeometrySource if not already.
        # z=_Z_UNSET means the user didn't pass z → auto-detect a column.
        # z=None (default) → colour by index; z="col" → use that column.
        if not isinstance(data, GeometrySource):
            source = GeometrySource(
                data,
                z=z,
                units=units,
                metadata=metadata or {},
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

        # Infer domain from geometries if none is set
        if self.domain is None and geometries:
            from earthkit.plots.geography import domains
            from earthkit.plots.geography.bounds import BoundingBox

            bbox = None
            for geom in geometries:
                if geom is not None:
                    try:
                        geom_bbox = BoundingBox.from_geometry(geom, source_crs=source_crs)
                        bbox = geom_bbox if bbox is None else bbox + geom_bbox
                    except Exception:
                        pass
            if bbox is not None:
                self.domain = domains.Domain(list(bbox), crs=bbox.crs)

        # When colouring by index, build a Style with one discrete colour per
        # shape so each geometry gets a distinct colour.
        if style is None and source.value_name == "index":
            from earthkit.plots.styles import Style as _Style

            n = len(geometries)
            style = _Style(
                colors=kwargs.pop("colors", kwargs.pop("cmap", "tab20")),
                levels=list(range(n + 1)),
                legend_style=None,
            )
            auto_style = False

        # Configure style
        style = configure_style("add_geometries", style, source, units, auto_style, kwargs)
        style_kwargs = style.to_add_geometries_kwargs(data_values)

        # Prepare scalar mappable for colorbar
        if data_values is not None:
            scalar_mappable = ScalarMappable(norm=style_kwargs["norm"], cmap=style_kwargs["cmap"])
            scalar_mappable.set_array(data_values)
        else:
            scalar_mappable = None

        # Render geometries
        collection = self.ax.add_geometries(
            geometries,
            crs=source_crs,
            **{**style_kwargs, **kwargs},
        )

        # Create layer for colorbar/legend management
        layer = Layer(source, collection, self, style)
        if scalar_mappable is not None:
            layer._scalar_mappable = scalar_mappable
            layer._units = source.units
            layer._value_name = source.value_name
        self.layers.append(layer)

        # Add labels if requested
        if labels:
            label_column = labels if not isinstance(labels, bool) else source._column
            self._add_choropleth_labels(source, label_column, exclude_nan_labels=exclude_nan_labels, **kwargs)

        return self.layers[-1]

    def _add_choropleth_labels(self, source, label_column=None, exclude_nan_labels=True, **kwargs):
        """
        Add labels to choropleth geometries.

        Parameters
        ----------
        source : GeometrySource
            The GeometrySource with geometries, data, and metadata.
        label_column : str, optional
            Column name to use for labels, or a template string with format
            specifiers. Supports Python format specification mini-language.

        Examples
        --------
            - "country_name" - Direct column reference
            - "{name}: {value:.1f} {units}" - Template with formatting
        exclude_nan_labels : bool, optional
            Whether to exclude labels for geometries where the z-value is NaN.
        **kwargs
            Additional keyword arguments (e.g., adjust_labels).
        """
        import re
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
            return

        # Build metadata dict from source.
        # Use source.units (applied/target units after conversion) for "units",
        # so label templates like "{units}" reflect the plotted units, not source units.
        metadata_keys = ["long_name", "standard_name", "variable_name", "name"]
        source_metadata = {}
        for key in metadata_keys:
            value = source.metadata(key)
            if value is not None:
                source_metadata[key] = value
        if source.units is not None:
            source_metadata["units"] = source.units

        # Parse template to detect units format spec
        units_format_spec = None
        has_units_placeholder = False
        template_for_formatting = label_column
        if is_template and "units" in source_metadata:
            has_units_placeholder = re.search(r"\{units(?::[^}]+)?\}", label_column) is not None
            units_match = re.search(r"\{units:([^}]+)\}", label_column)
            if units_match:
                units_format_spec = units_match.group(1)
                template_for_formatting = re.sub(r"\{units:[^}]+\}", "{units}", label_column)
            elif has_units_placeholder:
                units_format_spec = "~E"

        # Build records for _add_polygon_labels
        records = []
        z_col = source._column  # name of the z column (None if index colouring)
        for pos, (idx, row) in enumerate(gdf.iterrows()):
            if exclude_nan_labels and data_values is not None:
                if np.isnan(data_values[pos]):
                    continue

            record = SimpleNamespace()
            record.geometry = row.geometry

            if is_template:
                formatter = {col: row[col] for col in gdf.columns if col != "geometry"}
                # Inject converted value for z column so templates use target units
                if z_col is not None and z_col in formatter and data_values is not None:
                    formatter[z_col] = data_values[pos]
                formatter.update(source_metadata)

                if has_units_placeholder and "units" in formatter:
                    from earthkit.plots.metadata import units as metadata_units

                    formatter["units"] = metadata_units.format_units(formatter["units"], format=units_format_spec)

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

                record.attributes = {"__label__": label_text}
                label_key_to_use = "__label__"
            else:
                record.attributes = {label_column: row[label_column]}
                label_key_to_use = label_column

            records.append(record)

        self._add_polygon_labels(
            records,
            label_key=label_key_to_use,
            adjust_labels=kwargs.get("adjust_labels", False),
        )

    @chainable_method
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
            The location of the legend(s). Must be a valid matplotlib legend
            location string (e.g. ``"upper right"``, ``"lower left"``).
            See :func:`matplotlib.pyplot.legend` for the full list.
        **kwargs
            Additional keyword arguments passed to :func:`matplotlib.pyplot.legend`.
        """
        from earthkit.plots.components.layers import Layer
        from earthkit.plots.sources import get_source

        if style is not None:
            dummy = [[1, 2], [3, 4]]
            self.contourf(x=dummy, y=dummy, z=dummy, style=style)
            mappable = self.layers[-1].mappable
            # Create a dummy source for legend creation
            dummy_source = get_source(dummy, x=dummy, y=dummy, z=dummy)
            layer = Layer(dummy_source, mappable, self, style)
            return layer.style.legend(layer, label=kwargs.pop("label", ""), **kwargs)
        else:
            for i, layer in enumerate(self.distinct_legend_layers):
                if isinstance(location, (list, tuple)):
                    loc = location[i]
                else:
                    loc = location
                if layer.style is not None:
                    layer._generate_legend(location=loc, **kwargs)
            return None

    @chainable_method
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
        return self.ax.gridlines(*args, **kwargs)

    @chainable_method
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
