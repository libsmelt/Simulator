# python-graph
# Makefile


# Module directories -------------------------------------------------

CORE_DIR="core/"
DOT_DIR="dot/"
TESTS_DIR="tests/"
DOCS_DIR="docs/"
TEMP="temp/"
PYTHONPATH="`pwd`/core:`pwd`/dot"
PYTHON="python"
PYTHON3="python3"


# General ------------------------------------------------------------

nothing:

sdist: clean sdist-core sdist-dot
	rm -rf dist
	mkdir dist
	cp */dist/* dist


# Core ---------------------------------------------------------------

install-core:
	cd ${CORE_DIR} && ./setup.py install

sdist-core: clean
	cd ${CORE_DIR} && ./setup.py sdist


# Dot ----------------------------------------------------------------

install-dot:
	cd ${DOT_DIR} && ./setup.py install

sdist-dot: clean
	cd ${DOT_DIR} && ./setup.py sdist


# Docs ---------------------------------------------------------------

docs: cleanpyc
	rm -rf ${DOCS_DIR} ${TEMP}
	mkdir -p ${TEMP}
	cp -R ${CORE_DIR}/pygraph ${TEMP}
	cp -Rn ${DOT_DIR}/pygraph ${TEMP}/pygraph/
	epydoc -v --no-frames --no-sourcecode --name="python-graph" \
		--url="https://github.com/Shoobx/python-graph" \
		--inheritance listed --no-private --html \
		--graph classtree \
		--css misc/epydoc.css -o docs ${TEMP}/pygraph/*.py \
		${TEMP}/pygraph/algorithms/*py \
		${TEMP}/pygraph/algorithms/heuristics/*.py \
		${TEMP}/pygraph/algorithms/filters/* \
		${TEMP}/pygraph/readwrite/* \
		${TEMP}/pygraph/classes/*.py \
		${TEMP}/pygraph/mixins/*.py
		rm -rf ${TEMP}


# Tests --------------------------------------------------------------

test-pre:
	reset

test: test-pre
	PYTHONPATH=${PYTHONPATH} ${PYTHON} tests/testrunner.py

test3: test-pre
	PYTHONPATH=${PYTHONPATH} ${PYTHON3} tests/testrunner.py

tests: test


# Tests --------------------------------------------------------------

console:
	export PYTHONPATH=${PYTHONPATH} && cd ${TESTS_DIR} && ${PYTHON}

console3:
	export PYTHONPATH=${PYTHONPATH} && cd ${TESTS_DIR} && ${PYTHON3}


# Cleaning -----------------------------------------------------------

cleanpyc:
	find tests dot core -name *.pyc -exec rm {} \;
	find tests dot core -name __pycache__ -exec rm -rf {} \; -prune

clean: cleanpyc
	rm -rf ${DOCS_DIR}
	rm -rf */dist
	rm -rf */build
	rm -rf */*.egg-info
	rm -rf dist


# Phony rules --------------------------------------------------------

.PHONY: clean cleanpyc docs-core
