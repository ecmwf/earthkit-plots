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

import warnings

import earthkit.data
import xarray as xr

from . import metadata, transformers
from .schema import schema


INPUT_ONLY_KWARGS = ["cyclic"]


def discard_input_only_kwargs(function):
    def wrapper(self, *args, **kwargs):
        result = function(self, *args, **kwargs)
        if result is not None:
            
            args, kwargs = result
            if kwargs.get("cyclic"):
                lengths = [len(kwargs[axis]) for axis in self.AXES]
                min_len = min(lengths)
                max_len = max(lengths)
                if min_len != max_len:
                    for axis in self.AXES:
                        if len(kwargs[axis]) == max_len-2:
                            kwargs[axis] = transformers.cyclify(kwargs[axis])

            for kwarg in INPUT_ONLY_KWARGS:
                result[1].pop(kwarg, None)
        return result
    return wrapper


@discard_input_only_kwargs
def xarray(self, data, args, kwargs):
    if isinstance(data, earthkit.data.core.Base):
        try:
            dataset = data.to_xarray().squeeze()
        except (NotImplementedError, ValueError):
            return None
    else:
        try:
            dataset = earthkit.data.from_object(data).to_xarray().squeeze()
        except (NotImplementedError, ValueError):
            return None

    if len(dataset.dims) != 1:
        raise ValueError(
            f"data must have exactly 1 dimension, but found "
            f"{len(dataset.dims)}; please reduce the data down to 1 dimension"
        )
    dim = list(dataset.dims)[0]

    data_vars = list(dataset.data_vars)

    axis_attrs = dict()
    assigned_attrs = [
        kwargs.get(axis).split(".")[-1] for axis in self.AXES if axis in kwargs
    ]
    for axis in self.AXES:
        hovertemplate = kwargs.get("hovertemplate")
        transformer = None
        attr = kwargs.get(axis)
        if isinstance(attr, str) and "." in attr:
            transformer = attr
            attr = attr.split(".")[-1]

        if attr is None:
            if dim not in list(axis_attrs.values())+assigned_attrs:
                attr = dim
            else:
                attr = data_vars[0]
                if len(data_vars) > 1:
                    warnings.warn(
                        f"dataset contains more than one data variable; "
                        f"variable '{attr}' has been selected for plotting"
                    )
                if "{axis}" in hovertemplate:
                    kwargs["hovertemplate"] = hovertemplate.format(axis=axis)

        kwargs[axis] = dataset[attr].values
        axis_attrs[axis] = attr
        if transformer is not None:
            kwargs = self.transform(transformer, axis, kwargs)

        if getattr(self.layout, f"{axis}axis").title.text is None:
            title = metadata.get_axis_title(dataset, attr)
            self.update_layout(**{f"{axis}axis": {"title": title}})

    return args, kwargs


@discard_input_only_kwargs
def numpy(self, data, args, kwargs):
    if isinstance(data, earthkit.data.core.Base):
        try:
            ndarray = data.to_numpy()
        except (NotImplementedError, ValueError):
            return None
    else:
        try:
            ndarray = earthkit.data.from_object(data).to_numpy()
        except (NotImplementedError, ValueError):
            return None

    x = kwargs.get("x")
    y = kwargs.get("y")
    if isinstance(x, str):
        kwargs = self.transform(x, "x", kwargs)
        x = kwargs["x"]
    if isinstance(y, str):
        kwargs = self.transform(y, "y", kwargs)
        y = kwargs["y"]

    if x is None and y is None:
        if ndarray.ndim == 1:
            y = ndarray
            x = list(range(len(y)))
        elif ndarray.ndim == 2:
            y, x = ndarray
        else:
            raise ValueError(
                f"data must have at most 2 dimensions, but found {ndarray.ndim}"
            )
    elif x is None:
        x = ndarray
    elif y is None:
        y = ndarray

    kwargs = {**kwargs, **{"x": x, "y": y}}

    return args, kwargs


@discard_input_only_kwargs
def plotly(self, data, args, kwargs):
    transformed_axes = []
    for axis in self.AXES:
        if isinstance(kwargs.get(axis), str):
            kwargs = self.transform(kwargs[axis], axis, kwargs)
            transformed_axes.append(axis)
    return args, kwargs
