FROM continuumio/miniconda3

WORKDIR /src/earthkit-plots

COPY environment.yml /src/earthkit-plots/

RUN conda install -c conda-forge gcc python=3.10 \
    && conda env update -n base -f environment.yml

COPY . /src/earthkit-plots

RUN pip install --no-deps -e .
