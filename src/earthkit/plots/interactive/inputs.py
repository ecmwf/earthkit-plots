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
import numpy as np

from earthkit.plots.interactive import times

# from earthkit.plots.schemas import schema


AXES = ["x", "y"]


def _earthkitify(data):
    if isinstance(data, (list, tuple)):
        data = np.array(data)
    if not isinstance(data, earthkit.data.core.Base):
        data = earthkit.data.from_object(data)
    return data


def to_xarray(data):
    return _earthkitify(data).to_xarray().squeeze()


def to_pandas(data):
    try:
        return _earthkitify(data).to_pandas()
    except NotImplementedError:
        return _earthkitify(data).to_xarray().squeeze().to_pandas()


def to_numpy(data):
    return _earthkitify(data).to_numpy()


def sanitise(axes=("x", "y"), multiplot=True):
    def decorator(function):
        def wrapper(
            data=None,
            *args,
            time_frequency=None,
            time_aggregation="mean",
            aggregation=None,
            deaccumulate=False,
            **kwargs,
        ):
            time_axis = kwargs.pop("time_axis", None)
            traces = []
            if data is not None:
                ds = to_xarray(data)
                time_dim = times.guess_time_dim(ds)
                data_vars = list(ds.data_vars)
                if time_frequency is not None:
                    if isinstance(time_aggregation, (list, tuple)):
                        for i, var_name in enumerate(data_vars):
                            ds[var_name] = getattr(
                                ds[var_name].resample(**{time_dim: time_frequency}),
                                time_aggregation[i],
                            )()
                    else:
                        ds = getattr(
                            ds.resample(**{time_dim: time_frequency}), time_aggregation
                        )()
                    time_axis = 1
                if aggregation is not None:
                    ds = getattr(ds, aggregation)(dim=times.guess_non_time_dim(ds))
                    if "name" not in kwargs:
                        kwargs["name"] = aggregation
                if deaccumulate:
                    if isinstance(deaccumulate, str):
                        ds[deaccumulate] = ds[deaccumulate].diff(dim=time_dim)
                    else:
                        ds = ds.diff(dim=time_dim)
                if len(data_vars) > 1:
                    repeat_kwargs = {
                        k: v for k, v in kwargs.items() if k != "time_frequency"
                    }
                    repeat_kwargs
                    return [
                        wrapper(
                            ds[data_var], *args, time_axis=time_axis, **repeat_kwargs
                        )
                        for data_var in data_vars
                    ]
                if len(ds.dims) == 2 and multiplot:
                    expand_dim = times.guess_non_time_dim(ds)
                    for i in range(len(ds[expand_dim])):
                        kwargs["name"] = f"{expand_dim}={ds[expand_dim][i].item()}"
                        trace_kwargs = get_xarray_kwargs(
                            ds.isel(**{expand_dim: i}), axes, kwargs
                        )
                        traces.append(function(*args, **trace_kwargs))
                else:
                    trace_kwargs = get_xarray_kwargs(ds, axes, kwargs)
                    if not multiplot:
                        if time_axis is None:
                            time_axis = list(ds[data_vars[0]].dims).index(
                                times.guess_non_time_dim(ds)
                            )
                        trace_kwargs["time_axis"] = time_axis
                    traces.append(function(*args, **trace_kwargs))
            else:
                traces.append(function(*args, **kwargs))
            return traces

        return wrapper

    return decorator


def get_xarray_kwargs(data, axes, kwargs):
    data = to_xarray(data)
    kwargs = kwargs.copy()
    data_vars = list(data.data_vars)

    time_dim = times.guess_time_dim(data)
    dims = list(data.dims)
    non_time_dims = [d for d in dims if d != time_dim]

    axis_default = {
        "x": (
            time_dim
            if time_dim in dims
            else (non_time_dims[0] if non_time_dims else dims[-1])
        ),
        "y": data_vars[0],
    }

    axis_attrs = dict()
    assigned_attrs = [
        kwargs.get(axis).split(".")[-1] for axis in axes if axis in kwargs
    ]
    for axis in axes:
        attr = kwargs.get(axis)
        if attr is None:
            attr = axis_default.get(axis, dims[-1])
        else:
            attr = attr.split(".")[-1]
            if attr in axis_attrs.values() + assigned_attrs:
                attr = data_vars[0]
                if len(data_vars) > 1:
                    warnings.warn(
                        f"dataset contains more than one data variable; "
                        f"variable '{attr}' has been selected for plotting"
                    )

        kwargs[axis] = data[attr].values
        axis_attrs[axis] = attr

    return kwargs
