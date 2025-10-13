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
from pathlib import Path

import matplotlib.pyplot as plt
import yaml
from matplotlib import rcParams

from earthkit.plots._plugins import PLUGINS
from earthkit.plots.geo.coordinate_reference_systems import parse_crs
from earthkit.plots.utils.dict_utils import recursive_dict_update

_DEFAULT_SCHEMA = "default"


RCPARAMS = [
    "backends",
    "lines",
    "patches",
    "hatches",
    "font",
    "text",
    "latex",
    "axes",
    "dates",
    "xtick",
    "ytick",
    "grid",
    "figure",
    "images",
    "errorbar",
    "histogram",
    "agg",
    "paths",
    "saving",
    "interactive keymaps",
    "animation",
]


class SchemaNotFoundError(FileNotFoundError):
    pass


class _set:
    def __init__(self, schema, **kwargs):
        self.schema = schema

        keys = [key for key in kwargs if key in self.schema]

        self.old_kwargs = {key: self.schema.get(key) for key in keys}
        self.old_kwargs = {
            **self.old_kwargs,
            **{
                key: dict(value)
                for key, value in self.old_kwargs.items()
                if isinstance(value, Schema)
            },
        }

        self.new_kwargs = [key for key in kwargs if key not in self.schema]
        self.schema._update(**kwargs)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.schema._update(**self.old_kwargs)
        for key in self.new_kwargs:
            self.schema.pop(key, None)


class Schema(dict):
    """Class for containing and maintaining global style settings."""

    PROTECTED_KEYS = ["_parent"]

    parsers = {
        "reference_crs": parse_crs,
    }

    def __init__(self, parent=None, **kwargs):
        self._parent = parent
        self._update(**kwargs)
        self._apply_rcParams()

    def _apply_rcParams(self):
        if "style_sheet" in self:
            plt.style.use(self["style_sheet"])
        for param, config in self.items():
            if param in RCPARAMS and self._parent is None:
                for member, value in config.items():
                    if member in Schema.PROTECTED_KEYS:
                        continue
                    rcParams[".".join((param, member))] = value

    def __getattr__(self, key):
        if key in self:
            return self[key]
        raise AttributeError(key)

    def __setattr__(self, key, value):
        if isinstance(value, dict) and not isinstance(value, Schema):
            parent = f"{self._parent}.{key}" if self._parent else key
            value = Schema(parent=parent, **value)
        try:
            self[key] = value
        except KeyError:
            raise AttributeError(key)
        if self._parent in RCPARAMS and key not in Schema.PROTECTED_KEYS:
            rcParams[".".join((self._parent, key))] = value

    def __repr__(self):
        return f"{self.__class__.__name__}({super().__repr__()})"

    def _update(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.parsers:
                value = self.parsers[key](value)
            setattr(self, key, value)

    def apply(self, *keys):
        def decorator(function):
            @functools.wraps(function)
            def wrapper(*args, **kwargs):
                return function(*args, **self._update_kwargs(kwargs, keys))

            return wrapper

        return decorator

    def _update_kwargs(self, kwargs, keys):
        path = self._parent

        global schema

        schema_child = schema
        # Search for path in global schema
        while path:
            sub_path = path.split(".")[0]

            if sub_path not in schema_child:
                schema_child = Schema()
                break

            schema_child = schema_child.get(sub_path)
            path = ".".join(path.split(".")[1:])

        # Build kwargs with correct hierarchy:
        # 1. Start with init schema (values set at decorator initialisation)
        # 2. Override with global schema if found (specific schema values)
        # 3. Override with passed kwargs (highest priority)
        schema_kwargs = self._to_dict()
        global_kwargs = schema_child._to_dict()
        if global_kwargs:
            schema_kwargs = recursive_dict_update(schema_kwargs, global_kwargs)

        if keys:
            schema_kwargs = {
                key: schema_kwargs[key]
                for key in keys
                if key not in Schema.PROTECTED_KEYS
            }
        return recursive_dict_update(schema_kwargs, kwargs)

    def to_stylesheet(
        self,
        *,
        include_style_sheet: bool = True,
        drop_none: bool = True,
        as_list_when_sheet_present: bool = True,
        prepend: list | None = None,
        append: list | None = None,
    ):
        """
        Convert the schema to a Matplotlib stylesheet compatible object.

        Returns
        -------
        dict | list
            - If `include_style_sheet` is False or no `style_sheet` is present:
              returns a dict of rcParams (e.g., {"font.family": "DejaVu Sans", ...}).
            - If `include_style_sheet` is True and a `style_sheet` is present and
              `as_list_when_sheet_present` is True: returns a list layering
              [*prepend, style_sheet, rc_dict, *append].
              This is directly usable as `style=` in pytest-mpl.

        Parameters
        ----------
        include_style_sheet : bool
            If True and a top-level "style_sheet" key exists, include it *before*
            the flattened rcParams so your schema overrides the sheet where needed.
        drop_none : bool
            If True, drop rc entries whose value is None.
        as_list_when_sheet_present : bool
            If True, return a list when a style_sheet is present; otherwise merge
            only the rc dict (the caller would have to apply the sheet separately).
        prepend, append : list | None
            Optional extra styles (strings or dicts) to add before/after the schema.
        """

        def _flatten_section(section_name: str, section_value) -> dict:
            """Flatten a single top-level rc section to rcParams keys."""
            flat = {}
            # Typical case: nested mapping (Schema or dict)
            if isinstance(section_value, Schema):
                section_value = section_value._to_dict()
            if isinstance(section_value, dict):
                for k, v in section_value.items():
                    if k in Schema.PROTECTED_KEYS:
                        continue
                    if drop_none and v is None:
                        continue
                    flat[f"{section_name}.{k}"] = v
                return flat

            # Pragmatic special-case: allow `font: "DejaVu Sans"`
            if section_name == "font" and isinstance(section_value, str):
                flat["font.family"] = section_value
                return flat

            # Otherwise ignore non-mapping sections under RCPARAMS
            return flat

        # Build rc dict from top-level sections that belong to Matplotlib rcParams
        rc: dict = {}
        for section_name, section_value in self.items():
            if section_name in self.PROTECTED_KEYS:
                continue
            if section_name in RCPARAMS:
                rc.update(_flatten_section(section_name, section_value))

        # Optionally include style_sheet in a layered list
        sheet = self.get("style_sheet") if include_style_sheet else None
        has_sheet = isinstance(sheet, str) and bool(sheet)

        if has_sheet and as_list_when_sheet_present:
            out = []
            if prepend:
                out.extend(prepend)
            out.append(sheet)
            out.append(rc)
            if append:
                out.extend(append)
            return out

        if prepend or append:
            # Caller explicitly asked for layering; build the list even without a sheet.
            out = []
            if prepend:
                out.extend(prepend)
            if has_sheet:
                out.append(sheet)
            out.append(rc)
            if append:
                out.extend(append)
            return out

        # Default: just the rc dict
        return rc

    def _to_dict(self):
        d = dict()
        for key in self:
            if key in Schema.PROTECTED_KEYS:
                continue
            value = getattr(self, key)
            if isinstance(value, type(self)):
                value = value._to_dict()
            d[key] = value
        return d

    def set(self, **kwargs):
        """
        Set the value of a schema key.

        Parameters
        ----------
        **kwargs
            The schema keys and values to set.

        Example
        -------
        >>> schema.set(font="verdana")
        >>> with schema.set(font="comic sans"):
        ...     print(schema.font)
        ...
        comic sans
        >>> print(schema.font)
        verdana
        """
        return _set(self, **kwargs)

    def get(self, key):
        """
        Get the value of a schema key.

        Parameters
        ----------
        key : str
            The name of the schema key to get.

        Example
        -------
        >>> schema.set(font="verdana")
        >>> schema.get("font")
        'verdana'
        """
        return getattr(self, key)

    def use(self, name):
        """
        Use a named schema.

        Parameters
        ----------
        name : str
            The name of the schema to use, or path to a user-implemented schema.

        Example
        -------
        >>> schema.use("default")
        >>> schema.use("~/custom.yaml")
        """
        if name not in PLUGINS:
            file_name = Path(name).expanduser()
            if not file_name.exists():
                raise SchemaNotFoundError(f"No plugin '{name}' found")
        elif PLUGINS[name].get("schema") is None:
            raise SchemaNotFoundError(f"No schema found in '{name}' plugin")
        else:
            file_name = PLUGINS[name]["schema"]

        with open(file_name, "r") as f:
            kwargs = yaml.load(f, Loader=yaml.SafeLoader)

        self._reset(**kwargs)

    def _reset(self, **kwargs):
        self.__init__(**kwargs)


schema = Schema()
schema.use(_DEFAULT_SCHEMA)
