#!/bin/bash

pyflakes *.py; RC=$?
exit $RC
