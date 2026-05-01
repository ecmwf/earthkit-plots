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

import warnings

_TRANSFORMER_CACHE = {}


def reproject_geometries(geometries, src_crs, target_crs):
    """
    Reproject a list of shapely geometries from source CRS to target CRS.

    This is used as a performance optimisation to avoid on-the-fly reprojection
    during matplotlib rendering. It's suitable for features with many small
    segments (like coastlines) but not always for features with long straight lines
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
        src_proj = getattr(src_crs, "proj4_init", None) or src_crs.proj4_params
        target_proj = getattr(target_crs, "proj4_init", None) or target_crs.proj4_params

        src_pyproj = pyproj.CRS.from_proj4(src_proj) if not isinstance(src_proj, str) else pyproj.CRS(src_proj)
        tgt_pyproj = pyproj.CRS.from_proj4(target_proj) if not isinstance(target_proj, str) else pyproj.CRS(target_proj)

        cache_key = (src_pyproj.to_wkt(), tgt_pyproj.to_wkt())
        transformer = _TRANSFORMER_CACHE.get(cache_key)
        if transformer is None:
            transformer = pyproj.Transformer.from_crs(src_pyproj, tgt_pyproj, always_xy=True)
            _TRANSFORMER_CACHE[cache_key] = transformer

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
                    RuntimeWarning,
                )
                continue

        return reprojected

    except Exception as e:
        # If reprojection fails entirely, warn and return original geometries
        warnings.warn(
            f"Geometry reprojection failed: {e}. Falling back to cartopy reprojection.",
            RuntimeWarning,
        )
        return geometries
