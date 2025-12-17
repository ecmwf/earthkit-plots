from earthkit.plots.schemas import schema  # noqa: F401 - Initialize schema with default mplstyle

from earthkit.plots.core.subplots import Subplot
from earthkit.plots.temporal.timeseries import TimeSeries
from earthkit.plots.core.maps import Map
from earthkit.plots.core.figures import Figure

__all__ = ['Subplot', 'TimeSeries', 'Map', 'Figure', 'schema']