/*
 * Copyright (c) 2007, 2008, 2009, 2010, 2011, 2012, 2013 ETH Zurich.
 * All rights reserved.
 *
 * This file is distributed under the terms in the attached LICENSE file.
 * If you do not find this file, copies can be found by writing to:
 * ETH Zurich D-INFK, Universitaetstr. 6, CH-8092 Zurich. Attn: Systems Group.
 */

#include <stdio.h>
#include <stdbool.h>
#include <assert.h>

#include <unistd.h>

#include <sched.h>

int main(int argc, char **argv)
{
    int num_cores = sysconf(_SC_NPROCESSORS_ONLN);

    cpu_set_t mask;
    int sizemask = sched_getaffinity(0, sizeof(cpu_set_t), &mask);

    printf("Client up\n");
    for (int i = 0; i < num_cores; i++) {
        if (CPU_ISSET(i, &mask))
            printf("--running on core %d\n", i);
    }

    while (true) ; // Don't terminate
}
