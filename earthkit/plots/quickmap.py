
from earthkit.plots.components.figures import Figure
from earthkit.plots.schemas import schema


def _quickmap(function):
    def wrapper(*args, **kwargs):
        figure = Figure()
        subplot = figure.add_map()
        getattr(subplot, function.__name__)(*args, **kwargs)
        for method in schema.quickmap_workflow:
            getattr(subplot, method)()
        return subplot

    return wrapper


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
def block(*args, **kwargs):
    """Quick plot"""


@_quickmap
def contour(*args, **kwargs):
    """Quick plot"""


@_quickmap
def contourf(*args, **kwargs):
    """Quick plot"""
