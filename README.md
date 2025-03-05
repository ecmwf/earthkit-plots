<p align="center">
  <picture>
    <source srcset="https://raw.githubusercontent.com/ecmwf/logos/refs/heads/main/logos/earthkit/earthkit-plots-dark.svg" media="(prefers-color-scheme: dark)">
    <img src="https://raw.githubusercontent.com/ecmwf/logos/refs/heads/main/logos/earthkit/earthkit-plots-light.svg" height="80">
  </picture>
</p>

<p align="center">
  <a href="https://github.com/ecmwf/codex/raw/refs/heads/main/ESEE">
    <img src="https://github.com/ecmwf/codex/raw/refs/heads/main/ESEE/foundation_badge.svg" alt="Static Badge">
  </a>&nbsp;
  <a href="https://github.com/ecmwf/codex/raw/refs/heads/main/Project%20Maturity">
    <img src="https://github.com/ecmwf/codex/raw/refs/heads/main/Project%20Maturity/incubating_badge.svg" alt="Maturity: Incubating">
  </a>&nbsp;
  <a href="https://opensource.org/licenses/apache-2-0">
      <img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License: Apache 2.0">
    </a>&nbsp;
    <a href="https://pypi.python.org/pypi/earthkit-plots/">
      <img src="https://badge.fury.io/py/earthkit-plots.svg" alt="PyPI version fury.io">
  </a>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#installation">Installation</a> •
  <a href="https://earthkit-data.readthedocs.io/en/latest/">Documentation</a>
</p>

> \[!IMPORTANT\]
> This software is **Incubating** and subject to ECMWF's guidelines on [Software Maturity](https://github.com/ecmwf/codex/raw/refs/heads/main/Project%20Maturity).


**earthkit-plots** leverages the power of the **earthkit** ecosystem to make producing publication-quality scientific graphics as simple and convenient as possible.

⚡ **Concise, high-level API** – Generate high-quality visualisations with minimal code.

🧠 **Intelligent formatting** – Titles and labels automatically adapt based on common metadata standards.

🎨 **Customisable style libraries** – Easily swap styles to match your organisation, project, or personal preferences.

🔍 **Automatic data styling** – Detects metadata like variables and units to optionally apply appropriate formatting and styling.

🌍 **Complex grids supported out-of-the-box** - Visualise grids like HEALPix and reduced gaussian without any extra legwork.

## Quick Start

```python
import earthkit as ek

data = ek.data.from_source("sample", "test.grib")
ek.plots.quickplot(data)
```

## Installation

Install from PyPI:

```
python -m pip install earthkit-plots
```

More details, such as optional dependencies can be found at https://earthkit-plots.readthedocs.io/en/latest/install.html.

## License

```
Copyright 2022, European Centre for Medium Range Weather Forecasts.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

In applying this licence, ECMWF does not waive the privileges and immunities
granted to it by virtue of its status as an intergovernmental organisation
nor does it submit to any jurisdiction.
```