check: lint test

PY_SOURCE_FILES=mosec tests examples scripts setup.py
RUST_SOURCE_FILES=src/*

install:
	pip install -e .[dev,doc]
	pre-commit install

dev:
	cargo build
	mkdir -p mosec/bin
	cp ./target/debug/mosec mosec/bin/
	pip install -e .

test: dev
	echo "Running tests for the main logic"
	pytest tests -vv -s -m "not arrow"
	pip install -e .[plugin]
	sleep 1
	echo "Running tests for the plugin"
	pytest tests -vv -s -m "arrow"
	RUST_BACKTRACE=1 cargo test -vv

doc:
	mkdocs serve

clean:
	cargo clean
	rm -rf build/ dist/ site/ *.egg-info .pytest_cache
	find . -name '*.pyc' -type f -exec rm -rf {} +
	find . -name '__pycache__' -exec rm -rf {} +

package: clean
	PRODUCTION_MODE=yes python setup.py bdist_wheel

publish: package
	twine upload dist/*

format:
	autoflake --in-place --recursive ${PY_SOURCE_FILES}
	isort --project=mosec ${PY_SOURCE_FILES}
	black ${PY_SOURCE_FILES}
	cargo +nightly fmt --all

lint:
	isort --check --diff --project=mosec ${PY_SOURCE_FILES}
	black --check --diff ${PY_SOURCE_FILES}
	flake8 ${PY_SOURCE_FILES} --count --show-source --statistics
	mypy --install-types --non-interactive ${PY_SOURCE_FILES}
	cargo +nightly fmt -- --check

semantic_lint:
	cargo clippy

.PHONY: test doc
