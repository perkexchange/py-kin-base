
# default target does nothing
.DEFAULT_GOAL: default
default: ;

init:
	pip install .
	pip install -e .
	pip install pytest-cov ply mock pytest-asyncio asynctest
.PHONY: init

start:
	cd images && ./init.sh
	sleep 10
.PHONY: start

test:
	python -m pytest -v -rs --cov -s -x --fulltrace tests
.PHONY: test

codecov:
	pip install codecov
	python -m codecov
.PHONY: codecov

wheel:
	python setup.py bdist_wheel
.PHONY: wheel

pypi:
	twine upload dist/*
.PHONY: pypi

clean:
	find . -name \*.pyc -delete
.PHONY: clean

updatexdr:
	cd stellar_base/stellarxdr && python updatexdr.py && python xdrgen.py ../xdr/
.PHONY: updatexdr
