# Copyright 2026-, European Centre for Medium Range Weather Forecasts.
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

"""Matplotlib axes for thermodynamic diagrams."""

import functools

from matplotlib.axes import Axes

from earthkit.plots.thermodynamic.transforms import ThermoTransform


def _thermo_transform(method):
    """Make ``transform`` default to the (T, p) data coordinates of the diagram."""

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if kwargs.get("transform") is None:
            kwargs["transform"] = self.transThermoData
        return method(self, *args, **kwargs)

    return wrapper


class ThermoAxes(Axes):
    """
    Axes of a thermodynamic diagram.

    The native data coordinates of the axes are the diagram coordinates (x, y)
    of its :class:`~earthkit.plots.thermodynamic.transforms.DiagramGeometry`.
    The common plotting methods (``plot``, ``scatter``, ``fill_between``,
    ``fill_betweenx``, ``text``, ``annotate``, ``barbs``, ``quiver``) take their
    positions in temperature (°C) and pressure (hPa) instead, so that e.g.
    ``ax.plot(t, p)`` draws a sounding. Pass ``transform=ax.transData`` to use
    diagram coordinates, or any other transform as usual.

    Parameters
    ----------
    geometry : DiagramGeometry
        The geometry of the diagram.
    """

    name = "earthkit-thermo"

    def __init__(self, *args, geometry, **kwargs):
        # Must be set before Axes.__init__, which calls clear()
        self.geometry = geometry
        self.transThermo = ThermoTransform(geometry)
        super().__init__(*args, **kwargs)

    @property
    def transThermoData(self):
        """Transform from (T [°C], p [hPa]) to display coordinates."""
        return self.transThermo + self.transData

    def clear(self):
        super().clear()
        # The background lines replace the rectilinear grid, and the extent of
        # the diagram is set explicitly rather than from the data.
        self.grid(False)
        self.set_autoscale_on(False)
        if self.geometry.equal_aspect:
            self.set_aspect("equal", adjustable="box")
        self.tick_params(which="both", length=0)

    plot = _thermo_transform(Axes.plot)
    scatter = _thermo_transform(Axes.scatter)
    fill_between = _thermo_transform(Axes.fill_between)
    fill_betweenx = _thermo_transform(Axes.fill_betweenx)
    text = _thermo_transform(Axes.text)
    barbs = _thermo_transform(Axes.barbs)
    quiver = _thermo_transform(Axes.quiver)

    def annotate(self, text, xy, *args, **kwargs):
        if kwargs.get("xycoords") is None:
            kwargs["xycoords"] = self.transThermoData
        return super().annotate(text, xy, *args, **kwargs)

    def to_diagram(self, t, p):
        """Convert (T [°C], p [hPa]) to diagram coordinates (x, y)."""
        return self.geometry.forward(t, p)

    def from_diagram(self, x, y):
        """Convert diagram coordinates (x, y) to (T [°C], p [hPa])."""
        return self.geometry.inverse(x, y)
