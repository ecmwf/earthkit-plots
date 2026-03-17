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

import json
import logging
import re

LOG = logging.getLogger(__name__)

HEALPIX_PATTERN = re.compile(r"^[Hh]\d+$")
RGG_PATTERN = re.compile(r"^[OoNn]\d+$")

# Keys that are not part of the canonical gridspec and should be removed
_REMOVE_KEYS = {
    "j_points_consecutive",
    "i_scans_negatively",
    "j_scans_positively",
    "type",
}


class GridSpec:
    """
    A specification of a grid used in a Source.

    Wraps a dict representation of a grid specification, normalised from
    whatever earthkit-data version is installed.
    """

    def __init__(self, spec: dict):
        self._spec = spec

    @staticmethod
    def _first(data):
        if hasattr(data, "__len__") and not isinstance(data, dict):
            if len(data) == 0:
                return None
            return data[0]
        return data

    @staticmethod
    def _to_dict(raw) -> dict | None:
        """Convert a raw gridspec object (dict or earthkit GridSpec) to a plain dict."""
        if raw is None:
            return None
        if isinstance(raw, dict):
            d = dict(raw)
        elif isinstance(raw, str):
            # JSON string — common when attrs are round-tripped via NetCDF
            try:
                parsed = json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                return None
            if not isinstance(parsed, dict):
                return None
            d = parsed
        elif hasattr(raw, "_d"):
            # earthkit-data GridSpec / RawMetadata object
            d = dict(raw._d)
        else:
            return None

        # Remove scanning/type keys that are not part of the canonical spec
        for k in _REMOVE_KEYS:
            d.pop(k, None)

        return d if d else None

    @classmethod
    def from_data(cls, data):
        """
        Create a GridSpec from an earthkit-data Field or FieldList.

        Tries both the new API (field.geography.grid_spec) and the
        legacy API (field._metadata.geography.gridspec).
        """
        field = cls._first(data)
        if field is None:
            return None

        # New earthkit-data API: field.geography.grid_spec (property or callable)
        if hasattr(field, "geography"):
            geo = field.geography
            if geo is not None:
                raw = None
                # Try callable grid_spec() first, then property
                if hasattr(geo, "grid_spec"):
                    gs_attr = geo.grid_spec
                    try:
                        raw = gs_attr() if callable(gs_attr) else gs_attr
                    except Exception:
                        pass
                if raw is None and hasattr(geo, "gridspec"):
                    try:
                        raw = geo.gridspec()
                    except Exception:
                        pass
                spec = cls._to_dict(raw)
                if spec:
                    LOG.debug("GridSpec from field.geography: %s", spec)
                    return cls(spec)

        # Legacy earthkit-data API: field._metadata.geography.gridspec()
        if hasattr(field, "_metadata"):
            geo = getattr(field._metadata, "geography", None)
            if geo is not None and hasattr(geo, "gridspec"):
                try:
                    raw = geo.gridspec()
                    spec = cls._to_dict(raw)
                    if spec:
                        LOG.debug("GridSpec from _metadata.geography: %s", spec)
                        return cls(spec)
                except Exception:
                    pass

        return None

    def to_dict(self) -> dict:
        """Return the grid specification as a plain dict."""
        spec = self._spec.copy()

        # HEALPix requires an ordering key; default to "nested" if absent
        if self.name == "healpix":
            if not any(k in spec for k in ("ordering", "order")):
                spec["order"] = "nested"

        return spec

    @property
    def name(self) -> str:
        """Return the canonical grid name: 'healpix', 'reduced_gg', or 'unknown'."""
        grid = self._spec.get("grid")
        if isinstance(grid, str):
            if HEALPIX_PATTERN.match(grid):
                return "healpix"
            if RGG_PATTERN.match(grid):
                return "reduced_gg"
        return "unknown"


def get_grid_spec(data) -> GridSpec | None:
    """Return a GridSpec for *data*, or None if the grid type is not recognised."""
    return GridSpec.from_data(data)
