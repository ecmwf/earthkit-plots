import earthkit.data

import earthkit.plots

data = earthkit.data.from_source("sample", "era5-monthly-mean-2t-199312.grib")

earthkit.plots.quickplot(data)
