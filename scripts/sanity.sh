#!/bin/bash

function error() {
	echo $1
	exit 1
}

pyflakes *.py || error "Pyflakes failed"
vulture *.py  --exclude=brewer2mpl.py || error "Vulture failed"

exit 0
