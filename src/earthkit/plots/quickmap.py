import warnings

from earthkit.plots.components.figures import Figure
from earthkit.plots.schemas import schema


def _quickmap(function):
    def wrapper(*args, return_subplot=False, domain=None, **kwargs):
        figure = Figure()
        subplot = figure.add_map(domain=domain)
        try:
            getattr(subplot, function.__name__)(*args, **kwargs)
        except Exception as e:
            warnings.warn(
                f"Failed to execute {function.__name__} on given data; consider "
                "constructing the plot manually."
            )
            raise e
        for method in schema.quickmap_workflow:
            try:
                getattr(subplot, method)()
            except Exception:
                warnings.warn(
                    f"Failed to execute {method} on given data; consider "
                    "constructing the plot manually."
                )
        return subplot

    return wrapper


@_quickmap
def plot(*args, **kwargs):
    """Quick plot"""


@_quickmap
def line(*args, **kwargs):
    """Quick plot"""


@_quickmap
def bar(*args, **kwargs):
    """Quick plot"""


@_quickmap
def scatter(*args, **kwargs):
    """Quick plot"""


@_quickmap
def point_cloud(*args, **kwargs):
    """Quick plot"""


@_quickmap
def block(*args, **kwargs):
    """Quick plot"""


@_quickmap
def contour(*args, **kwargs):
    """Quick plot"""


@_quickmap
def contourf(*args, **kwargs):
    """Quick plot"""


@_quickmap
def quiver(*args, **kwargs):
    """Quick plot"""


@_quickmap
def barbs(*args, **kwargs):
    """Quick plot"""
