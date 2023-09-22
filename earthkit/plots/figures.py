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

import plotly.graph_objects as go

from . import inputs, transformers
from .schema import schema


class Figure(go.Figure):

    AXES = ("x", "y")
    _SANITISERS = (inputs.xarray, inputs.numpy, inputs.plotly)
    _TRANSFORMERS = (transformers.calendar.calendar,)

    from .envelopes import add_envelope

    def __init__(self, *args, schema=schema.figures.figure, **kwargs):
        super().__init__(*args, **schema._update_kwargs(kwargs))
        self._schema = schema
        self._trace_count = len(self.data)

    @classmethod
    def new_if_none(cls, schema=schema.figures.figure):
        def decorator(function):
            def wrapper(*args, fig=None, **kwargs):
                if fig is None:
                    fig = cls(schema=schema)
                elif not isinstance(fig, cls):
                    fig = cls(fig)
                return function(*args, fig=fig, **kwargs)
            return wrapper
        return decorator
    
    def sanitise(method):
        def wrapper(self, data=None, *args, **kwargs):
            args, kwargs = self._sanitise_input(data, args, kwargs)
            return method(self, *args, **kwargs)
        return wrapper

    def _sanitise_input(self, data, args, kwargs):
        kwargs = kwargs.copy()
        for sanitiser in self._SANITISERS:
            try:
                sanitised_input = sanitiser(self, data, args, kwargs)
            except NotImplementedError:  # from emohawk
                continue
            else:
                if sanitised_input is not None:
                    break
        else:
            raise TypeError(f"unable to handle input of type {type(data)}")
        
        args, kwargs = sanitised_input
        if "name" not in kwargs:
            kwargs["name"] = f"trace {self._trace_count}"

        return args, kwargs

    def count_traces(n_traces=1):
        def decorator(method):
            def wrapper(self, *args, **kwargs):
                result = method(self, *args, **kwargs)
                self._trace_count += n_traces
                return result
            return wrapper
        return decorator

    def transform(self, name, axis, kwargs):
        module, name = name.split(".")
        transformer = [t for t in self._TRANSFORMERS if module==t.__name__]
        if len(transformer)==0:
            raise ValueError(
                f"invalid transformer '{module}' for {self.__class__.__name__}; "
                f"must be one of {[t.__name__ for t in self._TRANSFORMERS]}"
            )
        transformer = transformer[0]
        kwargs = transformer(self, name, axis, kwargs)
        return kwargs

    @count_traces(n_traces=1)
    @schema.line.apply()
    @sanitise
    def add_line(self, *args, **kwargs):
        self._line(*args, **kwargs)
        return self

    def _line(self, *args, **kwargs):
        self.add_trace(go.Scatter(*args, **kwargs))

    @schema.scatter.apply()
    @sanitise
    @count_traces(n_traces=1)
    def add_scatter(self, *args, **kwargs):
        self._scatter(*args, **kwargs)
        return self

    def _scatter(self, *args, **kwargs):
        self.add_trace(go.Scatter(*args, **kwargs))

    @schema.bar.apply()
    @sanitise
    @count_traces(n_traces=1)
    def add_bar(self, *args, **kwargs):
        self._bar(*args, **kwargs)
        return self

    def _bar(self, *args, **kwargs):
        self.add_trace(go.Bar(*args, **kwargs))
    
    @count_traces(n_traces=1)
    def add_stripes(self, *args, diverging=True, divergence_point=0, **kwargs):
        hoverprecision = schema.settings.hoverprecision
        if diverging:
            hoverprecision = f"+{hoverprecision}"
        with schema.settings.set(hoverprecision=hoverprecision):
            result = self._add_stripes(
                *args,
                diverging=diverging, divergence_point=divergence_point,
                **kwargs,
            )
        return result

    @schema.stripes.apply()
    @sanitise
    def _add_stripes(self, *args, diverging, divergence_point, **kwargs):

        z = kwargs.pop("y", kwargs.pop("z", None))

        zmin = min(z)
        zmax = max(z)

        if diverging:
            abs_zmax = max(zmax - divergence_point, divergence_point - zmin)
            zmax = divergence_point + abs_zmax
            zmin = divergence_point - abs_zmax
            kwargs["colorscale"] = kwargs.pop("colorscale", "RdBu_r")

        self._heatmap(*args, y=[1]*len(z), z=z, zmin=zmin, zmax=zmax, **kwargs)
        return self


    def _heatmap(self, *args, **kwargs):
        self.add_trace(go.Heatmap(*args, **kwargs))

    add_envelope = count_traces(n_traces=1)(add_envelope)

    def format_hovertemplate(self, hovertemplate):
        return hovertemplate

    def next_color(self):
        return self._schema.layout.colorway[len(self.data)]
