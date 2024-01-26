import earthkit.plots


def test_version() -> None:
    assert earthkit.plots.__version__ != "999"
