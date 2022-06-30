TESTS = tests

VENV ?= .venv
CODE = tests app

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: venv
venv:
ifeq ($(OS), Windows_NT)
	python -m venv $(VENV)
	$(VENV)/Scripts/python -m pip install --upgrade pip
	$(VENV)/Scripts/python -m pip install poetry
	$(VENV)/Scripts/poetry install
else
	python3.9 -m venv $(VENV)
	$(VENV)/bin/python -m pip install --upgrade pip
	$(VENV)/bin/python -m pip install poetry
	$(VENV)/bin/poetry install
endif

.PHONY: up
up:
ifeq ($(OS), Windows_NT)
	$(VENV)/Scripts/python app/app.py
else
	$(VENV)/bin/python app/app.py
endif

.PHONY: test
test: ## Runs pytest
ifeq ($(OS), Windows_NT)
	$(VENV)/Scripts/pytest -v tests
else
	$(VENV)/bin/pytest -v tests
endif

.PHONY: lint
lint: ## Lint code
ifeq ($(OS), Windows_NT)
	$(VENV)/Scripts/flake8 --jobs 4 --statistics --show-source $(CODE)
	$(VENV)/Scripts/pylint --jobs 4 --rcfile=setup.cfg $(CODE)
	$(VENV)/Scripts/mypy $(CODE)
	$(VENV)/Scripts/black --skip-string-normalization --check $(CODE)
else
	$(VENV)/bin/flake8 --jobs 4 --statistics --show-source $(CODE)
	$(VENV)/bin/pylint --jobs 4 --rcfile=setup.cfg $(CODE)
	$(VENV)/bin/mypy $(CODE)
	$(VENV)/bin/black --skip-string-normalization --check $(CODE)
endif

.PHONY: format
format: ## Formats all files
ifeq ($(OS), Windows_NT)
	$(VENV)/Scripts/isort $(CODE)
	$(VENV)/Scripts/black --skip-string-normalization $(CODE)
	$(VENV)/Scripts/autoflake --recursive --in-place --remove-all-unused-imports $(CODE)
	$(VENV)/Scripts/unify --in-place --recursive $(CODE)
else
	$(VENV)/bin/isort $(CODE)
	$(VENV)/bin/black --skip-string-normalization $(CODE)
	$(VENV)/bin/autoflake --recursive --in-place --remove-all-unused-imports $(CODE)
	$(VENV)/bin/unify --in-place --recursive $(CODE)
endif

.PHONY: ci
ci:	lint test ## Lint code then run tests

.PHONY: check
check: test format lint ## Fast check and fix

.PHONY: run
run:
	cd app && flask run
