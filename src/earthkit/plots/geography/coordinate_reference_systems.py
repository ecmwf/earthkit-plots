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

DEFAULT_CRS = ccrs.PlateCarree()

CYLINDRICAL_COORDINATE_SYSTEMS = [
    ccrs.LambertCylindrical,
    ccrs.Mercator,
    ccrs.Miller,
    ccrs.PlateCarree,
]

CANNOT_TRANSFORM_FIRST = [
    ccrs.NorthPolarStereo,
    ccrs.SouthPolarStereo,
]

CRS_MAPPING = {
    "EPSG:4326": ccrs.PlateCarree,
    "cylindrical": ccrs.PlateCarree,
}


def dict_to_crs(kwargs):
    """
    Convert a dictionary representation of a CRS into a cartopy CRS.

    Parameters
    ----------
    crs : dict
        A dictionary representation of a CRS to be parsed and converted into a
        cartopy CRS. Must include a "name" key matching the name of a cartopy
        CRS, plus and keyword arguments to be passed to the CRS constructor.

    Example
    -------
    >>> earthkit.maps.domains.parse_crs(
    ...     {"name": "PlateCarree", "central_longitude": 50}
    ... )
    <Derived Projected CRS: +proj=eqc +ellps=WGS84 +a=6378137.0 +lon_0=50 +to_ ...>
    Name: unknown
    Axis Info [cartesian]:
    - E[east]: Easting (unknown)
    - N[north]: Northing (unknown)
    - h[up]: Ellipsoidal height (metre)
    Area of Use:
    - undefined
    Coordinate Operation:
    - name: unknown
    - method: Equidistant Cylindrical
    Datum: unknown
    - Ellipsoid: WGS 84
    - Prime Meridian: Greenwich

    Returns
    -------
    cartopy.crs.CRS
    """
    crs = getattr(ccrs, kwargs.pop("name"))
    return crs(**kwargs)


def string_to_crs(string):
    """
    Convert a string name of a CRS into a cartopy CRS.

    Parameters
    ----------
    crs : dict
        A string matching the name of a cartopy CRS.

    Example
    -------
    >>> earthkit.maps.domains.parse_crs("PlateCarree")
    <Derived Projected CRS: +proj=eqc +ellps=WGS84 +a=6378137.0 +lon_0=0.0 +to ...>
    Name: unknown
    Axis Info [cartesian]:
    - E[east]: Easting (unknown)
    - N[north]: Northing (unknown)
    - h[up]: Ellipsoidal height (metre)
    Area of Use:
    - undefined
    Coordinate Operation:
    - name: unknown
    - method: Equidistant Cylindrical
    Datum: unknown
    - Ellipsoid: WGS 84
    - Prime Meridian: Greenwich

    Returns
    -------
    cartopy.crs.CRS
    """
    try:
        crs = getattr(ccrs, string)()
    except AttributeError:
        raise ValueError(f"cartopy has no CRS named '{string}'")
    return crs


def parse_crs(crs):
    """
    Convert a string or dictionary representation of a CRS into a cartopy CRS.

    Parameters
    ----------
    crs : str, dict or cartopy.crs.CRS
        Some representation of a CRS to be parsed and converted into a cartopy
        CRS.
        If a string, must be the name of a cartopy CRS.
        If a dictionary, must include a "name" key matching the name of a
        cartopy CRS, plus and keyword arguments to be passed to the CRS
        constructor.

    Example
    -------
    >>> earthkit.maps.domains.parse_crs("PlateCarree")
    <Derived Projected CRS: +proj=eqc +ellps=WGS84 +a=6378137.0 +lon_0=0.0 +to ...>
    Name: unknown
    Axis Info [cartesian]:
    - E[east]: Easting (unknown)
    - N[north]: Northing (unknown)
    - h[up]: Ellipsoidal height (metre)
    Area of Use:
    - undefined
    Coordinate Operation:
    - name: unknown
    - method: Equidistant Cylindrical
    Datum: unknown
    - Ellipsoid: WGS 84
    - Prime Meridian: Greenwich
    >>> earthkit.maps.domains.parse_crs(
    ...     {"name": "PlateCarree", "central_longitude": 50}
    ... )
    <Derived Projected CRS: +proj=eqc +ellps=WGS84 +a=6378137.0 +lon_0=50 +to_ ...>
    Name: unknown
    Axis Info [cartesian]:
    - E[east]: Easting (unknown)
    - N[north]: Northing (unknown)
    - h[up]: Ellipsoidal height (metre)
    Area of Use:
    - undefined
    Coordinate Operation:
    - name: unknown
    - method: Equidistant Cylindrical
    Datum: unknown
    - Ellipsoid: WGS 84
    - Prime Meridian: Greenwich

    Returns
    -------
    cartopy.crs.CRS
    """
    if not isinstance(crs, (ccrs.CRS, type(None))):
        if isinstance(crs, dict):
            crs = dict_to_crs(crs)
        else:
            if crs in CRS_MAPPING:
                crs = CRS_MAPPING[crs]()
            elif crs.upper().startswith("EPSG"):
                crs = crs.upper().lstrip("EPSG:")
                crs = ccrs.epsg(crs)
            else:
                crs = string_to_crs(crs)

    return crs


def crs_equal(crs_a, crs_b=None, match_type_only=False):
    """
    Test whether two cartopy CRS instances are equivalent.

    Cartopy CRS objects do not implement ``__eq__`` based on their parameters,
    so two separately constructed ``ccrs.PlateCarree()`` objects compare as
    not-equal even though they represent the same projection.  This function
    compares by type and ``proj4_params`` instead.

    Parameters
    ----------
    crs_a : cartopy.crs.CRS
        First CRS to compare.
    crs_b : cartopy.crs.CRS, optional
        Second CRS to compare.  Defaults to ``ccrs.PlateCarree()`` — the CRS
        used by Natural Earth shapefiles — so callers can write
        ``crs_equal(self.crs)`` to test whether the map projection matches the
        Natural Earth source CRS without constructing a temporary object.
    match_type_only : bool, optional
        If True, only compare the CRS type (class), ignoring parameters such as
        ``central_longitude``.  Useful when the source data is in a fixed
        variant of a projection (e.g. Natural Earth in PlateCarree(-180..180))
        and the map uses the same projection family but with different
        parameters — cartopy handles the coordinate offset internally so no
        reprojection is needed.

    Returns
    -------
    bool
    """
    if crs_b is None:
        crs_b = DEFAULT_CRS
    if match_type_only:
        return type(crs_a) is type(crs_b)
    return type(crs_a) is type(crs_b) and crs_a.proj4_params == crs_b.proj4_params


def is_cylindrical(crs):
    """
    Determine whether a CRS is cylindrical.

    Parameters
    ----------
    crs : cartopy.crs.CRS
        The coordinate reference system for which to determine whether is is
        cyclindrical.

    Returns
    -------
    bool
    """
    return any(isinstance(crs, candidate) for candidate in CYLINDRICAL_COORDINATE_SYSTEMS)
