#!/usr/bin/env python
#
# Copyright (c) 2013-2016, ETH Zurich.
# All rights reserved.
#
# This file is distributed under the terms in the attached LICENSE file.
# If you do not find this file, copies can be found by writing to:
# ETH Zurich D-INFK, Universitaetstr. 6, CH-8092 Zurich. Attn: Systems Group.

import numpy

## NOTE: We want this file with only dependencies on standart-library things
## Dependencies to own files are an absolut no-go

def statistics(l):
    """
    Print statistics for the given list of integers
    @return A tuple (mean, stderr, median, min, max)
    """
    if not isinstance(l, list) or len(l)<1:
        return None

    nums = numpy.array(l)

    m = nums.mean(axis=0)
    median = numpy.median(nums, axis=0)
    d = nums.std(axis=0)

    return (m, d, median, nums.min(), nums.max())
