PROJECT := earthkit-plots
CONDA := conda
CONDAFLAGS :=
COV_REPORT := html

default: qa unit-tests

setup:
	pre-commit install

qa:
	pre-commit run --all-files

image-tests:
	python -m pytest -vv -m mpl_image --test-images

generate-test-images:
	python -m pytest -vv -m mpl_image --mpl-generate-path=./tests/.earthkit-plots-test-images/baseline-images

unit-tests:
	python -m pytest -vv -m 'not notebook and not mpl_image' --cov=. --cov-report=$(COV_REPORT)
