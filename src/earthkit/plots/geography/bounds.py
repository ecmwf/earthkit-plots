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
import numpy as np

from earthkit.plots.geography import coordinate_reference_systems, optimisers

# Number of samples taken along each bbox edge when reprojecting between CRSs.
# Matches the densification pyproj's transform_bounds uses by default.
DENSIFY_POINTS = 21


class BoundingBox:
    @classmethod
    def from_geometry(
        cls,
        geometry,
        source_crs=coordinate_reference_systems.DEFAULT_CRS,
        target_crs=None,
    ):
        """
        Generate a tight bounding box around a geometry.

        Parameters
        ----------
        geometry : shapely.geometry
            A shapely geometry around which the bounding box should be drawn.
        source_crs : cartopy.crs.CRS, optional
            The coordinate reference system on which the geometry's coordinates
            are defined. If `None`, assumes a cylindrical lat-lon CRS.
        target_crs : cartopy.crs.CRS, optional
            The target coordinate reference system for the generated bounding
            box.

        Returns
        -------
        earthkit.plots.geography.bounds.BoundingBox
        """
        try:
            geometries = list(geometry.geoms)  # get sub-geometries, if present
        except AttributeError:
            geometries = [geometry]

        xs = np.concatenate([geom.boundary.xy[0] for geom in geometries])
        ys = np.concatenate([geom.boundary.xy[1] for geom in geometries])

        if target_crs is not None and target_crs != source_crs:
            xys = target_crs.transform_points(x=xs, y=ys, src_crs=source_crs)
            xs = [point[0] for point in xys]
            ys = [point[1] for point in xys]
        else:
            target_crs = source_crs

            if any(lon in (min(xs), max(xs)) for lon in (-180, 180)):
                xs = [x % 360 for x in xs]

        return cls(min(xs), max(xs), min(ys), max(ys), crs=target_crs)

    @classmethod
    def from_bbox(cls, bbox, source_crs=None, target_crs=None):
        """
        Generate a bounding box which completely contains another bounding box.

        The intended use case of this method is to generate a bounding box on
        a different coordinate reference system to an input bounding box,
        ensuring that the entire input bounding box is countained.

        Parameters
        ----------
        bbox : list or earthkit.plots.geography.bounds.BoundingBox
            The bounding box around which to generate a new bounding box. If a
            list, mus
        source_crs : cartopy.crs.CRS, optional
            The coordinate reference system of the source bounding box.  If
            `None` (default), assumes a cylindrical lat-lon CRS, unless the
            source bounding box is an `earthkit.plots.geography.bounds.BoundingBox`
            with its own CRS.
        target_crs : cartopy.crs.CRS, optional
            The coordinate reference system in which to generate a new bounding
            box which entriely contains the input bounding box. If `None`
            (default), attempts to find an "optimised" target CRS based on the
            domain extents.

        Returns
        -------
        earthkit.plots.geography.bounds.BoundingBox
        """
        bounds = list(bbox)

        if source_crs is None:
            try:
                source_crs = bbox.crs
            except AttributeError:
                source_crs = coordinate_reference_systems.DEFAULT_CRS

        if target_crs is None:
            return cls(*bounds, source_crs).to_optimised_bbox()

        if source_crs == target_crs:
            return cls(*bounds, source_crs)

        x_min, x_max, y_min, y_max = bounds

        corners = [
            target_crs.transform_point(x_min, y_min, source_crs),
            target_crs.transform_point(x_min, y_max, source_crs),
            target_crs.transform_point(x_max, y_max, source_crs),
            target_crs.transform_point(x_max, y_min, source_crs),
        ]

        # A bbox with x_min > x_max wraps the antimeridian. Interpolating
        # linearly between them would sweep the long way around the globe and
        # report a grossly inflated extent, so leave those to the corner-based
        # path below, which handles the wrap explicitly.
        wraps_antimeridian = x_min > x_max

        # A straight edge in the source CRS is generally curved in the target,
        # so the extreme values usually lie along an edge rather than at a
        # corner. Sampling the corners alone understates - and for projections
        # like polar stereographic degenerates - the true extent: every corner
        # of a [-180, 180] domain maps onto the same meridian, collapsing the
        # box to zero width. Sample along each edge instead.
        edge = np.linspace(0, 1, DENSIFY_POINTS)
        xs_span = x_min + (x_max - x_min) * edge
        ys_span = y_min + (y_max - y_min) * edge
        ones_x = np.ones_like(xs_span)
        ones_y = np.ones_like(ys_span)

        edge_x = np.concatenate([xs_span, xs_span, x_min * ones_y, x_max * ones_y])
        edge_y = np.concatenate([y_min * ones_x, y_max * ones_x, ys_span, ys_span])

        points = target_crs.transform_points(source_crs, edge_x, edge_y)
        px, py = points[:, 0], points[:, 1]

        # Points that cannot be represented in the target CRS come back as NaN;
        # they carry no information about the extent, so drop them rather than
        # letting them poison the min/max.
        finite = np.isfinite(px) & np.isfinite(py)
        if finite.any() and not wraps_antimeridian:
            px, py = px[finite], py[finite]
            x_min, x_max = float(px.min()), float(px.max())
            y_min, y_max = float(py.min()), float(py.max())
        else:
            # Nothing transformed cleanly; fall back to the corner values so
            # the caller still gets a usable (if approximate) box.
            x_min = min(corner[0] for corner in corners[:2])
            x_max = max(corner[0] for corner in corners[2:4])
            y_min = min(corner[1] for corner in [corners[0], corners[-1]])
            y_max = max(corner[1] for corner in corners[1:3])

        if coordinate_reference_systems.is_cylindrical(target_crs):
            if (abs(corners[2][0] - corners[3][0]) > 180) or (abs(corners[0][0] - corners[1][0]) > 180):
                x_min = min([corner[0] % 360 for corner in corners[:2]])
                x_max = max([corner[0] % 360 for corner in corners[2:4]])
            if np.isclose(x_min, x_max):
                x_max += 360
            elif x_min > x_max:
                x_min %= 360
                x_max %= 360

        return cls(x_min, x_max, y_min, y_max, crs=target_crs)

    def __init__(
        self,
        x_min,
        x_max,
        y_min,
        y_max,
        crs=coordinate_reference_systems.DEFAULT_CRS,
    ):
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.crs = crs

    def __iter__(self):
        return iter((self.x_min, self.x_max, self.y_min, self.y_max))

    def __add__(self, second_bbox):
        second_bbox = second_bbox.to_bbox(self.crs)
        y_max = max(self.y_max, second_bbox.y_max)
        y_min = min(self.y_min, second_bbox.y_min)
        x_max = max(self.x_max, second_bbox.x_max)
        x_min = min(self.x_min, second_bbox.x_min)
        return BoundingBox(x_min, x_max, y_min, y_max, crs=self.crs)

    @property
    def north(self):
        """Convenience property to access this bbox's furthest north point."""
        return self.y_max

    @property
    def south(self):
        """Convenience property to access this bbox's furthest south point."""
        return self.y_min

    @property
    def east(self):
        """Convenience property to access this bbox's furthest east point."""
        return self.x_max

    @property
    def west(self):
        """Convenience property to access this bbox's furthest west point."""
        return self.x_min

    def to_optimised_bbox(self):
        """
        Generate a new bounding box using the "optimised" CRS for these extents.

        The method for choosing an optimised CRS is as follows:
            - If the area of the map is greater than 60% of the globe, use a
              global equirectangular CRS.
            - If the central latitude is within ±25 degrees, use an
              equirectangular CRS.
            - If the central latitude is greater (less) than +(-)75 degrees, use
              a North (South) Polar Stereo CRS.
            - If the central latitude falls between ±25 and ±75 degrees and the
              aspect ratio is > 0.8, use an Albers Equal Area CRS.
            - If the central latitude falls between ±25 and ±75 degrees and the
              aspect ratio is < 0.8, use a Transverse Mercator CRS.

        This method is adapted from the method used by
        https://projectionwizard.org,
        which is discussed in the following article:
        Šavrič, B., Jenny, B. and Jenny, H. (2016). Projection Wizard – An
        online map projection selection tool. The Cartographic Journal, 53–2, p.
        177–185.
        Doi: 10.1080/00087041.2015.1131938.

        Parameters
        ----------
        bounds : list
            The latitude and longitude extents of the bounding box, given as
            `[min_longitude, max_longitude, min_latitude, max_latitude]`.

        Returns
        -------
        cartopy.crs.CRS
        """
        layout = optimisers.Global(self.to_latlon_bbox)
        while True:
            new_layout = layout.mutate()
            if new_layout == layout:
                break
            else:
                layout = new_layout
        return BoundingBox.from_bbox(self, target_crs=layout.crs)

    @functools.cached_property
    def to_latlon_bbox(self):
        """
        Generate a tight bounding box around a geometry.

        Parameters
        ----------
        geometry : shapely.geometry
            A shapely geometry around which the bounding box should be drawn.
        source_crs : cartopy.crs.CRS, optional
            The coordinate reference system on which the geometry's coordinates
            are defined. If `None`, assumes a cylindrical lat-lon CRS.
        target_crs : cartopy.crs.CRS, optional
            The target coordinate reference system for the generated bounding
            box.

        Returns
        -------
        earthkit.plots.geography.bounds.BoundingBox
        """
        return self.to_bbox(target_crs=ccrs.PlateCarree())

    def to_bbox(self, target_crs):
        """
        Convert bounding box onto a new coordinate reference system.

        Paratemers
        ----------
        target_crs : cartopy.crs.CRS
            The coordinate reference system to use for the new bounding box.

        Returns
        -------
        earthkit.plots.geography.BoundingBox
        """
        return BoundingBox.from_bbox(self, target_crs=target_crs)

    def to_cartopy_bounds(self):
        """
        Convert bounding box to a cartopy-compatible list of bounds.

        Returns
        -------
        tuple
        """
        return (self.x_min, self.x_max, self.y_min, self.y_max)

    def contains_point(self, point, crs=None):
        """
        Determine whether or not a point lies within this bounding box.

        Parameters
        ----------
        point : tuple
            An x, y tuple representing the coordinates of the point.
        crs : cartopy.crs.CRS, optional
            The coordinate reference system on which the x and y coordinates of
            the given point are defined. If `None` (default), assumes the input
            point uses the same coordinate reference system as this bounding
            box.

        Returns
        -------
        bool
        """
        if None in self:
            raise ValueError("Cannot determine if point lies inside partially defined domain")
        if crs is not None:
            point = self.crs.transform_point(*point, crs)
        return (self.west <= point[0] <= self.east) and (self.south <= point[1] <= self.north)
