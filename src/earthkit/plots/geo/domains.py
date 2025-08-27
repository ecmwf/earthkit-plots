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
from shapely.geometry import Point, Polygon

from earthkit.plots.ancillary import load
from earthkit.plots.geo.bounds import BoundingBox
from earthkit.plots.geo.coordinate_reference_systems import DEFAULT_CRS, dict_to_crs
from earthkit.plots.identifiers import LATITUDE, LONGITUDE
from earthkit.plots.schemas import schema
from earthkit.plots.utils import string_utils

NO_TRANSFORM_FIRST = [
    ccrs.Stereographic,
    ccrs.NearsidePerspective,
    ccrs.TransverseMercator,
]

NO_BBOX = [
    ccrs.SouthPolarStereo,
    ccrs.NorthPolarStereo,
    ccrs.TransverseMercator,
]


def force_minus_180_to_180(x):
    """
    Force an array of longitudes to lie in [-180, +180],
    *but* preserve any original +180° values (so you don’t
    collapse the east edge onto the west edge).
    """
    x = np.asarray(x)
    x2 = (x + 180) % 360 - 180
    # now restore +180 wherever the original was exactly +180
    # (so that our grid retains its full span)
    x2 = np.where(np.isclose(x, 180), 180, x2)
    return x2


def roll_from_0_360_to_minus_180_180(x):
    """
    Find the index at which an array of longitudes crosses the 180° meridian.

    Parameters
    ----------
    x : array-like (1D or 2D)
        The longitudes to be checked.

    Returns
    -------
    int
        The index at which the array crosses 180°.
    """
    x = np.asarray(x)

    if x.ndim == 1:
        # Handle 1D longitude array
        idx = np.argwhere(x >= 180)
    elif x.ndim == 2:
        # Handle 2D longitude array (original behavior)
        idx = np.argwhere(x[0] >= 180)
    else:
        raise ValueError("Input array must be 1D or 2D.")

    if len(idx) == 0:
        raise ValueError("No longitude values found greater than or equal to 180°.")

    return idx[0][0]


def roll_from_minus_180_180_to_0_360(x):
    """
    Find the index at which an array of longitudes crosses the 0° meridian.

    Parameters
    ----------
    x : array-like
        The longitudes to be checked.
    """
    return np.argwhere(x[0] >= 0)[0][0]


def force_0_to_360(x):
    """
    Force an array of longitudes to be in the range 0 to 360.

    Parameters
    ----------
    x : array-like
        The longitudes to be forced into the range 0 to 360.
    """
    x2 = np.asarray(x % 360)
    x2 = np.where(np.isclose(x, 360), 360, x2)
    return x2


def is_latlon(data):
    """
    Determine whether a dataset' coordinates are in latitude and longitude.

    Parameters
    ----------
    data : xarray.Dataset or earthkit.data.core.Base
        The dataset to be checked.
    """
    dataset = data.to_xarray().squeeze()
    return all(
        any(name in dataset.dims for name in names) for names in (LATITUDE, LONGITUDE)
    )


def format_name(domain_name):
    """
    Format a domain name to match the lookup keys in the domain lookup.

    Parameters
    ----------
    domain_name : str
        The domain name to be formatted.
    """
    # normalise the input string and the lookup key
    domain_lookup = load("domains", data_type="geo")
    domain_name = domain_name.lower().replace("_", " ")
    name_mapping = {k.lower(): k for k in domain_lookup["domains"]}

    if domain_name not in name_mapping:
        for name, alt_names in domain_lookup["alternate_names"].items():
            if domain_name in [alt_name.lower() for alt_name in alt_names]:
                domain_name = name
                break
        else:
            domain_name = None
    domain_name = name_mapping.get(domain_name, domain_name)

    return domain_name


def union(domains, name=None):
    """
    Combine multiple domains into a single domain.

    Parameters
    ----------
    domains : list of Domain or str
        The domains to be combined.
    name : str, optional
        The name of the new domain.

    Example
    -------
    >>> union(["Norway", "Sweden", "Finland"], name="Fennoscandia")
    """
    domains = [
        domain if not isinstance(domain, str) else Domain.from_string(domain)
        for domain in domains
    ]
    if len(domains) > 1:
        domain = sum(domains[1:], domains[0])
    else:
        domain = domains[0]
    if name is not None:
        domain._name = name
    return domain


class Domain:
    """
    Class for storing domain information.

    Parameters
    ----------
    bbox : list of float
        The bounding box of the domain in the form [west, east, south, north].
    crs : cartopy.crs.CRS, optional
        The coordinate reference system of the domain.
    name : str, optional
        The name of the domain.
    """

    @classmethod
    def from_string(cls, string, crs=None):
        """
        Create a domain from a string.

        The name of the domain can be a country, region, or a custom domain as
        defined in the domain lookup associated with your schema.

        Parameters
        ----------
        string : str
            The name of the domain.
        crs : cartopy.crs.CRS, optional
            The coordinate reference system to be used.
        """
        from earthkit.plots.geo import natural_earth

        domain_name = format_name(string)
        domain_lookup = load("domains", data_type="geo")

        if domain_name is not None and domain_name in domain_lookup["domains"]:
            domain_config = domain_lookup["domains"][domain_name]
            if isinstance(domain_config, list):
                bounds = domain_config
                domain_crs = None
            else:
                bounds = domain_config.get("bounds")
                domain_crs = dict_to_crs(domain_config.get("crs"))

            if crs is not None:
                bbox = BoundingBox.from_bbox(
                    bounds,
                    source_crs=domain_crs,
                    target_crs=crs,
                )
            elif domain_crs is not None:
                bbox = BoundingBox(*bounds, crs=domain_crs)
            else:
                bbox = BoundingBox.from_bbox(
                    bounds,
                    source_crs=domain_crs,
                ).to_optimised_bbox()
            crs = bbox.crs
            bounds = list(bbox)

        else:
            domain_name = domain_name or string
            source = natural_earth.NaturalEarthDomain(domain_name, crs)
            domain_name = source.domain_name
            bounds = source.bounds
            crs = source.crs
        return cls(bounds, crs, domain_name)

    @classmethod
    def from_bbox(cls, *args, name=None, **kwargs):
        """
        Create a domain from a bounding box.

        Parameters
        ----------
        *args : list of float
            The bounding box of the domain in the form [west, east, south, north].
        name : str, optional
            The name of the domain.
        **kwargs
            Additional keyword arguments to be passed to the BoundingBox constructor.
        """
        bbox = BoundingBox.from_bbox(*args, **kwargs)
        return cls(list(bbox), crs=bbox.crs, name=name)

    @classmethod
    def from_data(cls, data):
        """
        Create a domain from a dataset.

        The domain will be created based on the bounding box and CRS of the
        dataset.

        Parameters
        ----------
        data : xarray.Dataset or earthkit.data.core.Base
            The dataset from which to create the domain.
        """
        bbox = [None, None, None, None]
        try:
            crs = data.projection().to_cartopy_crs()
        except AttributeError:
            if is_latlon(data):
                lons = data.to_points()["x"]
                if isinstance(lons[0], (list, np.ndarray)):
                    lons = lons[0]
                crs = ccrs.PlateCarree(central_longitude=lons[len(lons) // 2])
            else:
                raise ValueError("unable to determine CRS of data")
        return cls(bbox, crs=crs)

    def __init__(self, bbox, crs=DEFAULT_CRS, name=None):
        self.bbox = BoundingBox(*bbox, crs)
        self._name = name

    @property
    def name(self):
        """The name of the domain."""
        if isinstance(self._name, list):
            return string_utils.list_to_human(self._name)
        else:
            return self._name

    def __eq__(self, value):
        if not isinstance(value, Domain):
            return False
        return list(self.bbox) == list(value.bbox) and self.crs == value.crs

    def __add__(self, second_domain):
        if isinstance(self._name, list):
            if isinstance(second_domain._name, list):
                name = self._name + second_domain._name
            else:
                name = self._name + [second_domain._name]
        elif isinstance(second_domain._name, list):
            name = [self._name] + second_domain._name
        else:
            name = [self._name, second_domain._name]
        bbox = self.bbox + second_domain.bbox
        return Domain.from_bbox(bbox, name=name)

    @property
    def crs(self):
        """The coordinate reference system of the domain."""
        return self.bbox.crs

    @property
    def title(self):
        """The title of the domain."""
        if self.name is None:
            if self.bbox is None:
                string = "None"
            else:
                bounds = list(self.bbox.to_latlon_bbox())
                strings = []
                for value, ordinal in zip(bounds, "WESN"):
                    strings.append(f"{value:.5g}°" + (ordinal if value != 0 else ""))
                string = ", ".join(strings)
            return string
        return self.name

    @property
    def is_complete(self):
        """Whether the domain is fully defined."""
        return None not in list(self.bbox)

    @property
    def can_bbox(self):
        """Whether the domain can be used to slice data."""
        can_bbox = True
        if any(isinstance(self.crs, crs) for crs in NO_BBOX):
            can_bbox = False
        return can_bbox

    def extract(
        self,
        x,
        y,
        values=None,
        extra_values=None,
        source_crs=None,
    ):
        """
        Slice data to fit the domain. Works for both gridded and unstructured data.

        Parameters
        ----------
        x : array-like
            The x-coordinates of the data.
        y : array-like
            The y-coordinates of the data.
        values : array-like, optional
            The values of the data.
        extra_values : list of array-like, optional
            Additional values to be sliced.
        source_crs : cartopy.crs.CRS, optional
            The coordinate reference system of the input data.
        """
        # If source_crs is None, assume PlateCarree
        if source_crs is None:
            source_crs = ccrs.PlateCarree()
        x = np.array(x)
        y = np.array(y)
        if x.ndim == 1 and y.ndim == 1:
            x, y = np.meshgrid(x, y)

        values = np.array(values) if values is not None else None

        if values is not None and values.ndim == 3:
            additional_dim = values.shape[-1]
        else:
            additional_dim = None

        if self.is_complete and schema.crop_domain:
            crs_bounds = list(BoundingBox.from_bbox(self.bbox, self.crs, source_crs))

            # Handle longitude wrapping
            roll_by = None
            if crs_bounds[0] < 0:
                if crs_bounds[0] < np.array(x).min() and (x > 180).any():
                    roll_by = roll_from_0_360_to_minus_180_180(x)
                    x = force_minus_180_to_180(x)
                    for i in range(2):
                        crs_bounds[i] = force_minus_180_to_180(crs_bounds[i])
            elif crs_bounds[0] < 180 and crs_bounds[1] > 180 and (x >= 0).any():
                if crs_bounds[1] > x.max():
                    roll_by = roll_from_minus_180_180_to_0_360(x)
                    x = force_0_to_360(x)
                    for i in range(2):
                        crs_bounds[i] = force_0_to_360(crs_bounds[i])

            if roll_by is not None:
                if x.ndim == 1:
                    x = np.roll(x, roll_by)
                    y = np.roll(y, roll_by)
                    if values is not None:
                        values = np.roll(values, roll_by)
                    if extra_values is not None:
                        extra_values = [np.roll(v, roll_by) for v in extra_values]
                else:
                    x = np.roll(x, roll_by, axis=1)
                    y = np.roll(y, roll_by, axis=1)
                    if values is not None:
                        values = np.roll(values, roll_by, axis=1)
                    if extra_values is not None:
                        extra_values = [
                            np.roll(v, roll_by, axis=1) for v in extra_values
                        ]

            if self.can_bbox:
                # Determine if data is gridded or unstructured
                if x.ndim == 1 and y.ndim == 1:
                    # Pad the crs_bounds by 10%
                    _crs_bounds = [
                        crs_bounds[0] - 0.05 * (crs_bounds[1] - crs_bounds[0]),
                        crs_bounds[1] + 0.05 * (crs_bounds[1] - crs_bounds[0]),
                        crs_bounds[2] - 0.05 * (crs_bounds[3] - crs_bounds[2]),
                        crs_bounds[3] + 0.05 * (crs_bounds[3] - crs_bounds[2]),
                    ]
                    # Unstructured data: use point-in-polygon
                    polygon = Polygon(
                        [
                            (_crs_bounds[0], _crs_bounds[2]),
                            (_crs_bounds[1], _crs_bounds[2]),
                            (_crs_bounds[1], _crs_bounds[3]),
                            (_crs_bounds[0], _crs_bounds[3]),
                        ]
                    )
                    points = np.vstack([x, y]).T
                    mask = np.array(
                        [polygon.contains(Point(px, py)) for px, py in points]
                    )

                    x = x[mask]
                    y = y[mask]

                    if values is not None:
                        values = values[mask]
                    if extra_values is not None:
                        extra_values = [v[mask] for v in extra_values]

                else:
                    # Calculate grid resolution
                    resolution_x = (x.max() - x.min()) / x.shape[1]
                    resolution_y = (y.max() - y.min()) / y.shape[0]

                    # Calculate padding (roughly 1 degree's worth)
                    padding_cells = max(1, int(1 / max(resolution_x, resolution_y)))

                    # Check if we need to handle longitude wrapping
                    x_min = x.min()
                    x_max = x.max()

                    # Case 1: Data is 0-360, domain spans negative longitudes (e.g., Europe domain)
                    if x_min >= 0 and x_max <= 360 and crs_bounds[0] < 0:
                        # Roll data so that negative longitudes are at the end
                        roll_amount = int((360 - abs(crs_bounds[0])) / resolution_x)
                        # Ensure roll_amount is within reasonable bounds
                        roll_amount = max(0, min(roll_amount, x.shape[1] - 1))

                        x = np.roll(x, roll_amount, axis=1)
                        y = np.roll(y, roll_amount, axis=1)
                        if values is not None:
                            values = np.roll(values, roll_amount, axis=1)
                        if extra_values is not None:
                            extra_values = [
                                np.roll(v, roll_amount, axis=1) for v in extra_values
                            ]

                        # Adjust bounds to match rolled coordinates
                        adjusted_bounds = [
                            crs_bounds[0]
                            + 360,  # Shift negative longitudes to positive
                            crs_bounds[1],
                            crs_bounds[2],
                            crs_bounds[3],
                        ]
                    # Case 2: Data is -180 to 180, domain spans 0 meridian
                    elif (
                        x_min < 0
                        and x_max > 0
                        and crs_bounds[0] < 0
                        and crs_bounds[1] > 0
                    ):
                        # Roll data so that the domain is continuous
                        roll_amount = int((180 - crs_bounds[0]) / resolution_x)
                        # Ensure roll_amount is within reasonable bounds
                        roll_amount = max(0, min(roll_amount, x.shape[1] - 1))

                        x = np.roll(x, roll_amount, axis=1)
                        y = np.roll(y, roll_amount, axis=1)
                        if values is not None:
                            values = np.roll(values, roll_amount, axis=1)
                        if extra_values is not None:
                            extra_values = [
                                np.roll(v, roll_amount, axis=1) for v in extra_values
                            ]

                        adjusted_bounds = crs_bounds
                    else:
                        adjusted_bounds = crs_bounds

                    # Apply padding to the adjusted bounds
                    padded_bounds = [
                        adjusted_bounds[0] - padding_cells * resolution_x,
                        adjusted_bounds[1] + padding_cells * resolution_x,
                        adjusted_bounds[2] - padding_cells * resolution_y,
                        adjusted_bounds[3] + padding_cells * resolution_y,
                    ]

                    # Use boolean masking instead of searchsorted for more robust handling
                    bbox = np.where(
                        (x >= padded_bounds[0])
                        & (x <= padded_bounds[1])
                        & (y >= padded_bounds[2])
                        & (y <= padded_bounds[3]),
                        True,
                        False,
                    )

                    if bbox.any():
                        # Get the shape of the valid region
                        shape = bbox[
                            np.ix_(np.any(bbox, axis=1), np.any(bbox, axis=0))
                        ].shape

                        if shape[0] > 0 and shape[1] > 0:
                            x = x[bbox].reshape(shape)
                            y = y[bbox].reshape(shape)
                            if values is not None:
                                if additional_dim is not None:
                                    values = values[bbox].reshape(
                                        shape + (additional_dim,)
                                    )
                                else:
                                    values = values[bbox].reshape(shape)
                            if extra_values is not None:
                                extra_values = [
                                    v[bbox].reshape(shape) for v in extra_values
                                ]
                        else:
                            # Fallback: use original data if reshaping results in empty arrays
                            pass
                    else:
                        # Fallback: if no data found with padding, try without padding
                        bbox_fallback = np.where(
                            (x >= adjusted_bounds[0])
                            & (x <= adjusted_bounds[1])
                            & (y >= adjusted_bounds[2])
                            & (y <= adjusted_bounds[3]),
                            True,
                            False,
                        )

                        if bbox_fallback.any():
                            shape = bbox_fallback[
                                np.ix_(
                                    np.any(bbox_fallback, axis=1),
                                    np.any(bbox_fallback, axis=0),
                                )
                            ].shape

                            if shape[0] > 0 and shape[1] > 0:
                                x = x[bbox_fallback].reshape(shape)
                                y = y[bbox_fallback].reshape(shape)
                                if values is not None:
                                    if additional_dim is not None:
                                        values = values[bbox_fallback].reshape(
                                            shape + (additional_dim,)
                                        )
                                    else:
                                        values = values[bbox_fallback].reshape(shape)
                                if extra_values is not None:
                                    extra_values = [
                                        v[bbox_fallback].reshape(shape)
                                        for v in extra_values
                                    ]

        if not extra_values:
            return x, y, values
        else:
            return x, y, values, extra_values


class PresetDomain(Domain):
    BBOX = BoundingBox(-180, 180, -90, 90)
    CRS = ccrs.PlateCarree()
    NAME = "Custom Domain"

    def __init__(self, bbox=None, crs=None, name=None):
        if bbox is None:
            bbox = self.BBOX
        if crs is None:
            crs = self.CRS
        if name is None:
            name = self.NAME
        super().__init__(bbox=bbox, crs=crs, name=name)
