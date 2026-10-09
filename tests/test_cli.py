# (C) Copyright 2026 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import pytest

pytest.importorskip("earthkit.cli.standard_args")
pytest.importorskip("earthkit.data")

from click.testing import CliRunner  # noqa: E402
from earthkit.cli.main import earthkit  # noqa: E402
from earthkit.cli.standard_args import SOURCE_HELP  # noqa: E402

from earthkit.cli import plots as plots_cli  # noqa: E402


def _invoke(*args, exit_code=0):
    result = CliRunner().invoke(earthkit, [str(a) for a in args])
    assert result.exit_code == exit_code, result.output + repr(result.exception)
    return result


@pytest.fixture
def plotted(monkeypatch):
    """Replace earthkit.data.from_source and earthkit.plots.geo.plot, recording the data plotted and saved."""
    import earthkit.data as ekd

    import earthkit.plots as ekp

    calls = {}

    class _FieldList(list):
        # Like a FieldList, also accepts a list of indexes
        def __getitem__(self, index):
            if isinstance(index, list):
                return [super(_FieldList, self).__getitem__(i) for i in index]
            return super().__getitem__(index)

    class _Data:
        def to_fieldlist(self):
            return _FieldList(range(10))

    class _Chart:
        def save(self, path):
            calls["save"] = path

    def _plot(data, **kwargs):
        calls["data"] = data
        return _Chart()

    monkeypatch.setattr(ekd, "from_source", lambda *args, **kwargs: _Data())
    monkeypatch.setattr(ekp.geo, "plot", _plot)
    return calls


def test_cli_registers_plot():
    assert earthkit.get_command(None, "plot") is plots_cli.plot


def test_cli_plot_help():
    output = _invoke("plot", "--help").output
    assert "[OPTIONS] SOURCE\n" in output
    assert "-i, --index" in output
    # Only the common options of earthkit-utils have short flags
    for flag in ("-s,", "-d,", "-m,", "-u,", "-g,"):
        assert flag not in output
    # The shared description from earthkit-utils, rewrapped by click
    assert " ".join(SOURCE_HELP.split()) in " ".join(output.split())


@pytest.mark.parametrize(
    "index, expected",
    (
        ("3", 3),
        ("4,5,8", [4, 5, 8]),
        ("1:7:2", [1, 3, 5]),
    ),
)
def test_cli_plot_index(plotted, tmp_path, index, expected):
    _invoke("plot", "dummy:", "--index", index, "--save", tmp_path / "plot.png")
    assert plotted["data"] == expected
    assert plotted["save"] == str(tmp_path / "plot.png")


def test_cli_plot_invalid_index(plotted):
    result = _invoke("plot", "dummy:", "-i", "a", exit_code=2)
    assert "Invalid value for '-i' / '--index'" in result.output
