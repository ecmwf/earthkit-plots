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

import math
import warnings

from . import keywords, metadata
from .schema import schema


COMMON_BOUNDS_DIMS = [
    "quantile",
    "percentile",
]


@schema.envelope.apply()
def add_envelope(self, bounds, *args, dim=None, showlegend=True, **kwargs):
    """
    Parameters
    ----------
    showlegend : bool or str (optional)
        Determines whether or not a legend is drawn. Valid options are:
        - `True`(default), in which case one legend is drawn for the entire
          envelope
        - `False`, in which case no envelope is drawn
        - `"bounds"`, in which case a separate legend is drawn for each set of
          bounds in the envelope
        - `"all"`, in which case a legend is drawn for each trace in the
          envelope (not recommended, as some of the traces required for an
          envelope are invisible).
    """
    if not isinstance(bounds, (list, tuple)):
        if dim is None:
            dim = guess_bounds_dim(bounds)
        bounds = metadata.split_dim(bounds, dim)

    if keywords.get("line_color", kwargs) is None:
        kwargs["line_color"] = self.next_color()

    auto_line_width = False
    if keywords.get("line_width", kwargs) is None:
        kwargs["line_width"] = 0
        auto_line_width = True

    ntraces = len(bounds)
    for itrace, (lower, upper) in enumerate(iterate(bounds)):
        if auto_line_width and upper is None:
            kwargs["line_width"] = schema.line.line_width
        lower_args, lower_kwargs = self._sanitise_input(lower, args, kwargs)
        legend_kwargs = get_legend_kwargs(self, showlegend, itrace*2, ntraces, **kwargs)
        self._line(*lower_args, **{**lower_kwargs, **legend_kwargs})
        if upper is not None:
            upper_args, upper_kwargs = self._sanitise_input(upper, args, kwargs)
            legend_kwargs = get_legend_kwargs(self, showlegend, itrace*2+1, ntraces, **kwargs)
            self._line(*upper_args, fill="tonexty", **{**upper_kwargs, **legend_kwargs})
    
    return self


def get_legend_kwargs(figure, showlegend, itrace, ntraces, **kwargs):
    legend_kwargs = dict()
    if showlegend is True:
        legendgroup = kwargs.get("name", f"trace {len(figure.data)-itrace}")
        legend_kwargs["legendgroup"] = kwargs.get("legendgroup", legendgroup)
        legend_kwargs["showlegend"] = itrace==1
    elif showlegend is False:
        legend_kwargs["showlegend"] = False
    elif showlegend == "all":
        warnings.warn(
            "legendmode \"all\" is not recommended except for debugging; some "
            "envelope traces are trasparent and will produce an unusual legend"
        )
        legend_kwargs["showlegend"] = True
    elif showlegend == "bounds":
        group_trace = (len(figure.data)-math.ceil((itrace)/2))
        legendgroup = kwargs.get("name", f"trace {group_trace}")
        legend_kwargs["showlegend"] = bool(itrace%2) or itrace+1 == ntraces
        legend_kwargs["legendgroup"] = kwargs.get("legendgroup", legendgroup)
    else:
        raise ValueError(
            f"showlegend got invalid value '{showlegend}'; must be one of "
            f"True, False, 'bounds' or 'all'"
        )
    return legend_kwargs


def iterate(bounds):
    """
    Iterate over envelope bounds, yielding each lower-upper pair.

    Parameters
    ----------
    bounds : list
        A list of bounds to plot as one or more envelopes, in ascending order
        (i.e. lowest to highest).
    
    Yields
    ------
    tuple
        The lower and upper bounds to plot as an envelope
    """
    for i in range(len(bounds)//2):
        yield bounds[i], bounds[-i-1]
    if len(bounds)%2:
        yield bounds[len(bounds)//2], None


def legend_kwargs(figure, showlegend, kwargs):
    if showlegend is True:
        pass
    elif showlegend is False:
        kwargs["showlegend"] = False
    elif showlegend == "once":
        legendgroup = kwargs.get("name", f"trace {len(figure.data)}")
        kwargs["legendgroup"] = kwargs.get("legendgroup", legendgroup)
    elif showlegend == "all":
        kwargs["showlegend"] = True
    else:
        raise ValueError(
            f"invalid option for showlegend '{showlegend}'; must be one of: "
            f"True, False, 'once', 'all'"
        )


def guess_bounds_dim(dataarray):
    for dim in COMMON_BOUNDS_DIMS:
        if dim in dataarray.dims:
            break
    else:
        raise TypeError(
            "Could not infer data dimension over which to split for envelope "
            "bounds; please pass the 'dim' argument matching the name of the "
            "dimension over which envelope bounds should be split."
        )
    return dim