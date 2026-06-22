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

notebook-tests:
	find docs/examples/examples docs/examples/gallery -mindepth 2 -name '*.ipynb' -not -name '_*' -not -path '*/.ipynb_checkpoints/*' -print0 \
		| PYDEVD_DISABLE_FILE_VALIDATION=1 xargs -0 jupyter nbconvert --to notebook --execute --stdout > /dev/null
