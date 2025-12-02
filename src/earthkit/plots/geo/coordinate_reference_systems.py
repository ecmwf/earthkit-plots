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

# EPSG codes that need special handling with custom cartopy projections
# These are EPSG codes that either don't work well with ccrs.epsg() or need
# specific parameters for optimal cartopy compatibility
EPSG_EXCEPTIONS = {
    "32661": lambda: ccrs.Stereographic(
        central_latitude=90,
        central_longitude=0,
        false_easting=2000000,
        false_northing=2000000,
        true_scale_latitude=81.114528,  # Corresponds to scale factor k=0.994
        globe=ccrs.Globe(ellipse='WGS84')
    ),
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
                epsg_code = crs.upper().lstrip("EPSG:")
                # Check if this EPSG code needs special handling
                if epsg_code in EPSG_EXCEPTIONS:
                    crs = EPSG_EXCEPTIONS[epsg_code]()
                else:
                    crs = ccrs.epsg(epsg_code)
            else:
                crs = string_to_crs(crs)

    return crs


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
    return any(
        isinstance(crs, candidate) for candidate in CYLINDRICAL_COORDINATE_SYSTEMS
    )
