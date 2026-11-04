.PHONY: install dev test lint format run

install:
	pip install -r requirements.txt

dev:
	pip install -r requirements-dev.txt

test:
	python -m pytest

lint:
	ruff check .

format:
	ruff check . --fix

run:
	uvicorn app.main:app --reload --port 8000
