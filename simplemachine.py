#!/usr/bin/env python
#
# Copyright (c) 2013-2016, ETH Zurich.
# All rights reserved.
#
# This file is distributed under the terms in the attached LICENSE file.
# If you do not find this file, copies can be found by writing to:
# ETH Zurich D-INFK, Universitaetstr. 6, CH-8092 Zurich. Attn: Systems Group.
import model

class SimpleMachine(model.Model):

    def get_name(self):
        return 'SimpleMachine'

    def get_num_numa_nodes(self):
        return 1

    def get_num_cores(self):
        return len(self.graph.nodes())

    def get_root_node(self):
        return self.graph.nodes()[0]

