import earthkit.data

import earthkit.plots.quickmap as qmap

data = earthkit.data.from_source("sample", "era5-monthly-mean-2t-199312.grib")

qmap.plot(data)
