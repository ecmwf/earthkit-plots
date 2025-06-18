PROJECT := earthkit-plots
CONDA := conda
CONDAFLAGS :=
COV_REPORT := html

default: qa unit-tests type-check

setup:
	pre-commit install

qa:
	pre-commit run --all-files

image-tests:
	python -m pytest -vv -m mpl_image --test-images --mpl --mpl-generate-summary=html --mpl-results-path=mpl-results

generate-test-images:
	python -m pytest -vv -m mpl_image --mpl-generate-path=/Users/mavj/ek/test-images/images/

unit-tests:
	python -m pytest -vv -m 'not notebook and not mpl_image' --cov=. --cov-report=$(COV_REPORT)
# python -m pytest -v -m "notebook"

# type-check:
# 	python -m mypy .

conda-env-update:
	$(CONDA) env update $(CONDAFLAGS) -f environment.yml

docker-build:
	docker build -t $(PROJECT) .

docker-run:
	docker run --rm -ti -v $(PWD):/srv $(PROJECT)

template-update:
	pre-commit run --all-files cruft -c .pre-commit-config-cruft.yaml

docs-build:
	cd docs && rm -fr _api && make clean && make html

#integration-tests:
#    python -m pytest -vv --cov=. --cov-report=$(COV_REPORT) tests/integration*.py
#    python -m pytest -vv --doctest-glob='*.md'
