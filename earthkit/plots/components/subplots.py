# Copyright 2024, European Centre for Medium Range Weather Forecasts.
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

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

from earthkit.plots import utils, identifiers
from earthkit.plots.metadata.formatters import LayerFormatter, SubplotFormatter, SourceFormatter
from earthkit.plots.sources import get_source, single
from earthkit.plots.schemas import schema
from earthkit.plots.components.layers import Layer
from earthkit.plots.styles import Style, _STYLE_KWARGS


DEFAULT_FORMATS = ['%Y', '%b', '%-d', '%H:%M', '%H:%M', '%S.%f']
ZERO_FORMATS = ['%Y', '%b\n%Y', '%-d\n%b %Y', '%H:%M', '%H:%M', '%S.%f']


class Subplot:
    
    def __init__(self, row=0, column=0, figure=None, **kwargs):
        self._figure = figure
        self._ax = None
        self._ax_kwargs = kwargs
        
        self.layers = []

        self.row = row
        self.column = column
        
        self.domain = None
    
    def set_major_xticks(self, frequency=None, format=None, highlight=None, highlight_color="red", **kwargs):
        formats = DEFAULT_FORMATS
        if frequency is None:
            locator = mdates.AutoDateLocator(maxticks=30)
        else:
            if frequency.startswith("D"):
                interval = frequency.lstrip("D") or 1
                if interval is not None:
                    interval = int(interval)
                locator = mdates.DayLocator(interval=interval, **kwargs)
            elif frequency.startswith("M"):
                interval = int(frequency.lstrip("M") or "1")
                locator = mdates.MonthLocator(interval=interval)
            elif frequency.startswith("Y"):
                locator = mdates.YearLocator()
            elif frequency.startswith("H"):
                interval = int(frequency.lstrip("H") or "1")
                locator = mdates.HourLocator(interval=interval)

        if format:
            formats = [format]*6
                    
        formatter = mdates.ConciseDateFormatter(
            locator, formats=formats, zero_formats=ZERO_FORMATS, show_offset=False)
        self.ax.xaxis.set_major_locator(locator)
        self.ax.xaxis.set_major_formatter(formatter)
        
        if highlight is not None:
            dates = [mdates.num2date(i) for i in self.ax.get_xticks()]
            for i, date in enumerate(dates):
                highlight_this = False
                for key, value in highlight.items():
                    attr = getattr(date, key)
                    attr = attr if not callable(attr) else attr()
                    if isinstance(value, list):
                        if attr in value:
                            highlight_this = True
                    else:
                        if attr == value:
                            highlight_this = True
                if highlight_this:
                    self.ax.get_xticklabels()[i].set_color(highlight_color)


    def set_minor_xticks(self, frequency=None):
        if frequency is None:
            locator = mdates.AutoDateLocator(maxticks=30)
        else:
            if frequency.startswith("D"):
                interval = int(frequency.lstrip("D") or "1")
                locator = mdates.DayLocator(interval=interval)
        self.ax.xaxis.set_minor_locator(locator)
    
    def plot_2D(method_name=None):
        def decorator(method):
            def wrapper(self, data=None, x=None, y=None, z=None, style=None, units=None, **kwargs):
                return self._extract_plottables(
                    method_name or method.__name__,
                    data=data, x=x, y=y, z=z, style=style, **kwargs,
                )
            return wrapper
        return decorator
    
    def plot_box(method_name=None):
        def decorator(method):
            def wrapper(self, data=None, x=None, y=None, z=None, style=None, **kwargs):
                source = get_source(data=data, x=x, y=y, z=z)
                kwargs = {**self._plot_kwargs(source), **kwargs}
                m = getattr(self.ax, method_name or method.__name__)
                if source.extract_x() in identifiers.TIME:
                    positions = mdates.date2num(source.x_values)
                else:
                    positions = source.x_values
                widths = min(0.5, np.diff(positions).min() * 0.7)
                mappable = m(source.z_values, positions=positions, widths=widths, **kwargs)
                self.layers.append(Layer(source, mappable, self, style))
                if isinstance(source._x, str):
                    if source._x in identifiers.TIME:
                        locator = mdates.AutoDateLocator(maxticks=30)
                        formatter = mdates.ConciseDateFormatter(locator, formats=['%Y', '%b', '%-d %b', '%H:%M', '%H:%M', '%S.%f'])
                        self.ax.xaxis.set_major_locator(locator)
                        self.ax.xaxis.set_major_formatter(formatter)
                    else:
                        self.ax.set_xlabel(source._x)
                if isinstance(source._z, str):
                    self.ax.set_ylabel(source._z)
                return mappable
            return wrapper
        return decorator

    def plot_3D(method_name=None, extract_domain=False):
        def decorator(method):
            def wrapper(self, data=None, x=None, y=None, z=None, style=None, every=None, **kwargs):
                return self._extract_plottables(
                    method_name or method.__name__,
                    data=data, x=x, y=y, z=z, style=style, every=every, extract_domain=extract_domain, **kwargs,
                )
            return wrapper
        return decorator

    def plot_vector(method_name=None):
        def decorator(method):
            def wrapper(self, data=None, x=None, y=None, z=None, u=None, v=None, colors=False, every=None, **kwargs):
                source = get_source(data=data, x=x, y=y, z=z, u=u, v=v)
                kwargs = {**self._plot_kwargs(source), **kwargs}
                m = getattr(self.ax, method_name or method.__name__)
                
                x_values = source.x_values
                y_values = source.y_values
                u_values = source.u_values
                v_values = source.v_values
                
                if self.domain is not None:
                    x_values, y_values, _, [u_values, v_values] = self.domain.extract(
                        x_values, y_values, extra_values=[u_values, v_values], source_crs=source.crs,
                    )
                
                if every is None:
                    args = [x_values, y_values, u_values, v_values]
                else:
                    args = [
                        thin_array(x_values, every=every),
                        thin_array(y_values, every=every),
                        thin_array(u_values, every=every),
                        thin_array(v_values, every=every),
                    ]
                if colors:
                    if every is None:
                        args.append(source.magnitude_values)
                    else:
                        args.append(source.magnitude_values[::every, ::every])
                
                mappable = m(*args, **kwargs)
                self.layers.append(Layer(source, mappable, self))
                if isinstance(source._x, str):
                    self.ax.set_xlabel(source._x)
                if isinstance(source._y, str):
                    self.ax.set_ylabel(source._y)
                return mappable
            return wrapper
        return decorator

    def _extract_plottables(self, method_name, data=None, x=None, y=None, z=None, style=None, every=None, source_units=None, extract_domain=False, **kwargs):
        if source_units is not None:
            source = get_source(data=data, x=x, y=y, z=z, units=source_units)
        else:
            source = get_source(data=data, x=x, y=y, z=z)
        kwargs = {**self._plot_kwargs(source), **kwargs}
        
        if method_name == "contourf":
            source.regrid = True
        
        if style is None:
            style = Style(**{key: kwargs.pop(key) for key in _STYLE_KWARGS if key in kwargs})
        
        if (data is None and z is None) or (z is not None and not z):
            z_values = None
        else:
            z_values = style.convert_units(source.z_values, source.units)
            z_values = style.apply_scale_factor(z_values)
            
        if source.metadata("gridType", default=None) == "healpix" and method_name=="pcolormesh":
            from earthkit.plots.geo import healpix
            nest = source.metadata("orderingConvention", default=None) == "nested"
            kwargs["transform"] = self.crs
            mappable = healpix.nnshow(z_values, ax=self.ax, nest=nest, style=style, **kwargs)
        else:
            x_values = source.x_values
            y_values = source.y_values
            
            if every is not None:
                x_values = x_values[::every]
                y_values = y_values[::every]
                if z_values is not None:
                    z_values = z_values[::every, ::every]
            
            if self.domain is not None and extract_domain:
                x_values, y_values, z_values = self.domain.extract(
                    x_values, y_values, z_values, source_crs=source.crs,
                )
            mappable = getattr(style, method_name)(
                self.ax, x_values, y_values, z_values, **kwargs)
        self.layers.append(Layer(source, mappable, self, style))
        return mappable

    @property
    def figure(self):
        from earthkit.plots import Figure
        if self._figure is None:
            self._figure = Figure(1, 1)
            self._figure.subplots = [self]
        return self._figure
    
    @property
    def fig(self):
        return self.figure.fig
    
    @property
    def ax(self):
        if self._ax is None:
            self._ax = self.figure.fig.add_subplot(
                self.figure.gridspec[self.row, self.column], **self._ax_kwargs
            )
        return self._ax

    @property
    def _default_title_template(self):
        templates = [layer._default_title_template for layer in self.layers]
        if len(set(templates)) == 1:
            template = templates[0]
        else:
            title_parts = []
            for i, template in enumerate(templates):
                keys = [k for _, k, _, _ in SubplotFormatter().parse(template)]
                for key in set(keys):
                    template = template.replace("{" + key, "{" + key + f"!{i}")
                title_parts.append(template)
            template = utils.list_to_human(title_parts)
        return template

    @property
    def distinct_legend_layers(self):
        """Layers on this subplot which have a unique `Style`."""
        unique_layers = []
        for layer in self.layers:
            for legend_layer in unique_layers:
                if legend_layer.style == layer.style:
                    break
            else:
                unique_layers.append(layer)
        return unique_layers

    def _plot_kwargs(self, *args, **kwargs):
        return dict()
    
    def coastlines(self, *args, **kwargs):
        raise NotImplementedError
    
    def gridlines(self, *args, **kwargs):
        raise NotImplementedError
    
    @plot_2D()
    def line(self, *args, **kwargs):
        """"""
    
    def labels(self, data=None, label=None, x=None, y=None, **kwargs):
         source = get_source(data=data, x=x, y=y)
         labels = SourceFormatter(source).format(label)
         for label, x, y in zip(labels, source.x_values, source.y_values):
            self.ax.annotate(label, (x, y), **kwargs)
    
    @plot_2D()
    def bar(self, *args, **kwargs):
        """"""
    
    @schema.scatter.apply()
    @plot_2D()
    def scatter(self, *args, **kwargs):
        """"""

    @schema.boxplot.apply()
    @plot_box()
    def boxplot(self, *args, **kwargs):
        """"""
    
    @plot_3D(extract_domain=True)
    def pcolormesh(self, *args, **kwargs):
        """"""
    
    @schema.contour.apply()
    @plot_3D(extract_domain=True)
    def contour(self, *args, **kwargs):
        """"""
    
    @plot_3D(extract_domain=True)
    def contourf(self, *args, **kwargs):
        """"""
    
    @plot_3D()
    def tripcolor(self, *args, **kwargs):
        """"""
    
    @plot_3D()
    def tricontour(self, *args, **kwargs):
        """"""
    
    @plot_3D()
    def tricontourf(self, *args, **kwargs):
        """"""
    
    @schema.quiver.apply()
    @plot_vector()
    def quiver(self, *args, **kwargs):
        """"""
    
    @schema.barbs.apply()
    @plot_vector()
    def barbs(self, *args, **kwargs):
        """"""
    
    block = pcolormesh

    @schema.legend.apply()
    def legend(self, style=None, location=None, **kwargs):
        legends = []
        if style is not None:
            dummy = [[1, 2], [3, 4]]
            mappable = self.contourf(x=dummy, y=dummy, z=dummy, style=style)
            layer = Layer(single.SingleSource(), mappable, self, style)
            legend = layer.style.legend(layer, label=kwargs.pop("label", ""), **kwargs)
            legends.append(legend)
        else:
            for i, layer in enumerate(self.distinct_legend_layers):
                if isinstance(location, (list, tuple)):
                    loc = location[i]
                else:
                    loc = location
                if layer.style is not None:
                    legend = layer.style.legend(layer, location=loc, **kwargs)
                legends.append(legend)
        return legends

    @schema.title.apply()
    def title(self, label=None, unique=True, wrap=True, **kwargs):
        if label is None:
            label = self._default_title_template
        label = self.format_string(label, unique)
        plt.sca(self.ax)
        return plt.title(label, wrap=wrap, **kwargs)

    def format_string(self, string, unique=True, grouped=True):
        if not grouped:
            return utils.list_to_human(
                [LayerFormatter(layer).format(string) for layer in self.layers]
            )
        else:
            return SubplotFormatter(self, unique=unique).format(string)

    def show(self):
        return self.figure.show()


def thin_array(array, every=2):
    if len(array.shape) == 1:
        return array[::every]
    else:
        return array[::every, ::every]