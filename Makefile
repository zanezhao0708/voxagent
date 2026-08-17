.PHONY: install dev demo serve test lint

install:
	pip install -e '.[local]'

dev:
	pip install -e '.[local,dev]'

serve:
	python -m voxagent.server

demo:
	python -m voxagent.cli demo

test:
	pytest -q

lint:
	ruff check voxagent tests
