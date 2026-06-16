# # Copyright 2025-, European Centre for Medium Range Weather Forecasts.
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# #     http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.

# # Tests inspired by Anemoi use case:
# # https://github.com/ecmwf/anemoi-inference/blob/main/src/anemoi/inference/outputs/plot.py

# import earthkit.data
# import pytest

# import earthkit.plots
# from earthkit.plots import schema


# def _make_arrayfield(
#     field: earthkit.data.Field, *, drop_keys: list[str] | None = None
# ) -> earthkit.data.ArrayField:
#     data = field.to_numpy()
#     metadata = {
#         "param": field.metadata("param"),
#         "paramId": field.metadata("paramId"),
#         "variable_name": field.metadata("param"),  # Required for now
#         "shortName": field.metadata("shortName"),
#         "step": field.metadata("step"),
#         "units": field.metadata("units"),
#         "base_datetime": field.metadata("base_datetime"),
#         "valid_time": field.metadata("valid_time"),
#         "latitudes": field.grid_points()[0],
#         "longitudes": field.grid_points()[1],
#     }

#     if drop_keys:
#         for key in drop_keys:
#             metadata.pop(key, None)

#     return earthkit.data.ArrayField(data, metadata)


# @pytest.mark.mpl_image
# @pytest.mark.mpl_image_compare(style=schema.to_stylesheet())
# def test_anemoi_use_single():
#     temperature, pressure = earthkit.data.from_source(
#         "sample", "era5-2t-msl-1985122512.grib"
#     )
#     temperature = _make_arrayfield(temperature)
#     pressure = _make_arrayfield(pressure)

#     chart = earthkit.plots.Map(domain="Europe")
#     chart.quickplot(temperature, units="celsius")
#     chart.quickplot(pressure, units="hPa")

#     chart.legend(location="right")

#     chart.coastlines()

#     chart.title()
#     chart.gridlines()

#     return chart.fig


# @pytest.mark.mpl_image
# @pytest.mark.mpl_image_compare(style=schema.to_stylesheet())
# def test_anemoi_use_fieldlist():
#     temperature, pressure = earthkit.data.from_source(
#         "sample", "era5-2t-msl-1985122512.grib"
#     )
#     temperature = _make_arrayfield(temperature)
#     pressure = _make_arrayfield(pressure)

#     chart = earthkit.plots.quickplot(
#         earthkit.data.FieldList.from_fields([temperature, pressure]), mode="overlay"
#     )
#     return chart.fig


# @pytest.mark.mpl_image
# @pytest.mark.mpl_image_compare(style=schema.to_stylesheet())
# def test_anemoi_use_fieldlist_minimal():
#     temperature, pressure = earthkit.data.from_source(
#         "sample", "era5-2t-msl-1985122512.grib"
#     )
#     temperature = _make_arrayfield(
#         temperature, drop_keys=["units", "paramId", "shortName", "param"]
#     )
#     pressure = _make_arrayfield(
#         pressure, drop_keys=["units", "paramId", "shortName", "param"]
#     )

#     chart = earthkit.plots.quickplot(
#         earthkit.data.FieldList.from_fields([temperature, pressure]), mode="overlay"
#     )
#     return chart.fig
