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
import xarray as xr

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


# In src/earthkit/plots/interactive/inputs.py

# ... (keep your existing imports and helper functions like to_xarray, etc.) ...

# V-- REPLACE THE ENTIRE sanitise FUNCTION WITH THIS --V
def sanitise(axes=("x", "y"), is_2d=False): # Add the new is_2d flag
    def decorator(function):
        def wrapper(data=None, *args, **kwargs):
            traces = []
            if data is not None:
                ds = to_xarray(data)

                # --- NEW LOGIC FOR 2D PLOTS ---
                if is_2d:
                    # If it's a Dataset with multiple variables, plot each one
                    if isinstance(ds, xr.Dataset):
                        for var_name in ds.data_vars:
                            # Call the decorated function for each DataArray
                            trace = function(ds[var_name], *args, **kwargs)
                            traces.append(trace)
                    # If it's a single DataArray, just plot it
                    elif isinstance(ds, xr.DataArray):
                        trace = function(ds, *args, **kwargs)
                        traces.append(trace)
                    return traces # Return the list of traces for the Chart class

                # --- EXISTING LOGIC FOR 1D PLOTS ---
                # (This part remains mostly the same as before)
                data_vars = list(ds.data_vars)
                if len(data_vars) > 1:
                    # Handle multi-variable datasets by calling recursively
                    return [
                        wrapper(ds[data_var], *args, **kwargs)
                        for data_var in data_vars
                    ]

                # Logic for slicing 2D data into multiple 1D traces
                if len(ds.dims) == 2:
                    expand_dim = times.guess_non_time_dim(ds)
                    for i in range(len(ds[expand_dim])):
                        kwargs["name"] = f"{expand_dim}={ds[expand_dim][i].item()}"
                        trace_kwargs = get_xarray_kwargs(
                            ds.isel(**{expand_dim: i}), axes, kwargs.copy()
                        )
                        traces.append(function(*args, **trace_kwargs))
                else:
                    # Logic for a single 1D trace
                    trace_kwargs = get_xarray_kwargs(ds, axes, kwargs.copy())
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
    dim = list(data.dims)[-1]

    axis_attrs = dict()
    assigned_attrs = [
        kwargs.get(axis).split(".")[-1] for axis in axes if axis in kwargs
    ]
    for axis in axes:
        attr = kwargs.get(axis)
        if attr is None:
            if dim not in list(axis_attrs.values()) + assigned_attrs:
                attr = dim
            else:
                attr = data_vars[0]
                if len(data_vars) > 1:
                    warnings.warn(
                        f"dataset contains more than one data variable; "
                        f"variable '{attr}' has been selected for plotting"
                    )

        kwargs[axis] = data[attr].values
        axis_attrs[axis] = attr

    return kwargs
