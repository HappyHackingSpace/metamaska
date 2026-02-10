sources = metamaska

.PHONY: test format lint unittest coverage pre-commit clean hf-upload collect-data train

test: format lint unittest

format:
	uv run ruff format $(sources) tests
	uv run ruff check --fix $(sources) tests

lint:
	uv run ruff check $(sources) tests
	uv run mypy $(sources) tests

unittest:
	uv run pytest

coverage:
	uv run pytest --cov=$(sources) --cov-branch --cov-report=term-missing tests

pre-commit:
	uv run pre-commit run --all-files

hf-upload:
	hf upload happyhackingspace/metamaska $(sources)/models/ models/ --repo-type model
	hf upload happyhackingspace/metamaska data/processed/ data/ --repo-type dataset

collect-data:
	uv run scripts/collect_data.py

train:
	uv run scripts/train.py

clean:
	rm -rf .mypy_cache .pytest_cache
	rm -rf *.egg-info
	rm -rf .tox dist site
	rm -rf coverage.xml .coverage
