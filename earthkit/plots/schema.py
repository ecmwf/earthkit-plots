# Copyright 2023, European Centre for Medium Range Weather Forecasts.
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

import collections.abc
from string import Formatter


class Schema(dict):
    def __init__(self, **kwargs):
        self.update(**kwargs)

    def __getattr__(self, key):
        schema, key = self.magic_key(key)
        if key in schema:
            value = schema[key]
            return self._format_string(value)
        raise AttributeError(key)

    def __setattr__(self, key, value):
        if isinstance(value, dict) and not isinstance(value, Schema):
            value = Schema(**value)

        try:
            schema, key = self.magic_key(key)
        except AttributeError:
            schema = self

        try:
            schema[key] = value
        except KeyError:
            raise AttributeError(key)

    def __repr__(self):
        return f"{self.__class__.__name__}({super().__repr__()})"

    def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def apply(self):
        def decorator(function):
            def wrapper(*args, **kwargs):
                return function(*args, **self._update_kwargs(kwargs))

            return wrapper

        return decorator

    def _update_kwargs(self, kwargs):
        return _recursive_dict_update(self.to_dict(), kwargs)

    def to_dict(self):
        d = dict()
        for key in self:
            value = getattr(self, key)
            if isinstance(value, type(self)):
                value = value.to_dict()
            d[key] = value
        return d

    def set(self, **kwargs):
        return _set(self, **kwargs)

    def get(self, key):
        value = getattr(self, key)
        value = self._format_string(value)
        return value

    def _get_magic_key(self, key):
        magic_key, *kwarg = key.split("_")
        if magic_key in self:
            return magic_key, "_".join(kwarg)
        else:
            raise AttributeError(f"{self.__class__.__name__} has no attribute {key}")

    def magic_key(self, key):
        if key in self:
            return self, key
        magic_key, kwarg = self._get_magic_key(key)
        return self[magic_key], kwarg

    def _format_string(self, value):
        if isinstance(value, str) and "{" in value:
            keys = [i[1] for i in Formatter().parse(value) if i[1] is not None]

            format_keys = dict()
            for key in keys:
                sub_schema = schema
                format_key = key
                if "." in key:
                    *nested_schemas, nested_key = key.split(".")
                    for nested_schema in nested_schemas:
                        sub_schema = getattr(sub_schema, nested_schema)
                    format_key = "_".join(key.split("."))
                    value = value.replace(key, format_key)
                format_keys[format_key] = getattr(sub_schema, nested_key)
            value = value.format(**format_keys)

        return value


class _set:
    def __init__(self, schema, **kwargs):
        self.schema = schema

        keys = [
            self.schema._get_magic_key(key)[0]
            for key in kwargs
            if key not in self.schema
        ]
        keys += [key for key in kwargs if key in self.schema]

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
        self.schema.update(**kwargs)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.schema.update(**self.old_kwargs)
        for key in self.new_kwargs:
            self.schema.pop(key, None)


def _recursive_dict_update(d, u):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = _recursive_dict_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d


schema = Schema(
    **{
        "settings": {
            "hoverprecision": ".1f",
            "line": {
                # TODO: Make this work!
                "marker_threshold": 60,
            },
            "auto_label_axes": True,
            "hovertemplate": "%{{{{{{axis}}:{settings.hoverprecision}}}}}",
        },
        "figures": {
            "stripes": {
                "layout":{
                    "xaxis": {
                        "visible": False,
                    },
                    "yaxis": {
                        "visible": False,
                    },
                    "height": 300,
                    "margin": {"l": 0, "r": 0, "t": 0, "b": 0},
                },
            },
            "figure": {
                "layout": {
                    "plot_bgcolor": "white",
                    "xaxis": {
                        "zeroline": False,
                        "showline": False,
                        "showgrid": True,
                        "gridwidth": 1,
                        "gridcolor": "#EEEEEE",
                    },
                    "yaxis": {
                        "zeroline": False,
                        "showline": True,
                        "linecolor": "black",
                        "showgrid": False,
                    },
                    "colorway": [
                        "#636EFA",
                        "#EF553B",
                        "#00CC96",
                        "#AB63FA",
                        "#FFA15A",
                        "#19D3F3",
                        "#FF6692",
                        "#B6E880",
                        "#FF97FF",
                        "#FECB52",
                    ],
                    "hovermode": "x",
                },
            },
        },
        "calendar": {
            "hovertemplate": "{settings.hovertemplate}",
        },
        "line": {
            "line": {
                "width": 2,
                "shape": "linear",
            },
            "mode": "lines",
            "hovertemplate": "{settings.hovertemplate}",
            "marker": {
                "size": 6,
                "line_width": 2,
                "line_color": "white",
            },
        },
        "scatter": {
            "mode": "markers",
            "hovertemplate": "{settings.hovertemplate}",
        },
        "bar": {

        },
        "stripes": {
            "showscale": False,
            "hovertemplate": "%{{x}}: %{{z:{settings.hoverprecision}}}<extra></extra>",
        },
        "envelope": {
            "line": {
                "shape": "{line.line.shape}",
            },
            "hovertemplate": "{line.hovertemplate}",
            "mode": "lines",
        },
    }
)
