PROJECT := earthkit-plots
CONDA := conda
CONDAFLAGS :=
COV_REPORT := html

default: qa unit-tests type-check

setup:
	pre-commit install

qa:
	pre-commit run --all-files

setup-test-images:
	@echo "Checking for test images repository..."
	@if [ ! -d "tests/.earthkit-plots-test-images" ]; then \
		echo "Test images repository not found, cloning from GitHub..."; \
		cd tests && git clone https://github.com/ecmwf/earthkit-plots-test-images.git .earthkit-plots-test-images; \
		echo "Test images repository cloned successfully."; \
	else \
		echo "Test images repository already exists."; \
	fi

check-test-images-sync:
	@if [ -d "tests/.earthkit-plots-test-images/.git" ]; then \
		cd tests/.earthkit-plots-test-images && \
		if ! git diff --quiet || ! git diff --cached --quiet; then \
			echo "WARNING: There are uncommitted changes in tests/.earthkit-plots-test-images/"; \
			echo "This means your local baseline images may differ from those in GitHub."; \
			echo "Consider committing and pushing changes to keep baselines in sync."; \
			echo ""; \
		fi; \
	fi

image-tests: setup-test-images check-test-images-sync
	python -m pytest -vv -m mpl_image --test-images

generate-test-images: setup-test-images check-test-images-sync
	python -m pytest -vv -m mpl_image --mpl-generate-path=./tests/.earthkit-plots-test-images/baseline-images

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
