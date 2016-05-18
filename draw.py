# Draw result of evaluation

import helpers
import config
import subprocess
import shlex
import logging

class Output():

    color_map = [ "red", "green", "blue", "orange" ]
    height_per_core = 5
    scale_x = .05

    "Wrapper to enable visualization output to file"
    def __init__(self, name, model, topo):
        self.name = name
        self.model = model
        self.topo =  topo
        self.obj_per_node = dict()
        self.obj_per_core = dict()
        self.f = open(name, 'w')

        self.obj = []
        self.last_node = None

        self.cores = self.__core_label_to_y_index()

        for c in self.model.get_graph().nodes():
            # Label
            node_name = 'core_%s_label' % c
            self.__add_object(c, node_name)
            self.f.write("\\node (%s) at (0mm,%dmm) {%5s};\n" % \
                             (node_name, self._y_coord_for_core(c), c))

    def __add_object(self, core, label):
        """
        Keep track of objects for fit tikz class
        Assumes that the object printes last is shown all the way to the right
        """
        self.obj.append(label)
        cidx = int(self.model.get_numa_id(core))

        self.obj_per_node[cidx] = self.obj_per_node.get(cidx, []) + [label]
        self.obj_per_core[core] = self.obj_per_core.get(core, []) + [label]

        self.last_node = label

    def _y_coord_for_core(self, core):
        "Determines padding between cores"
        if not core in self.cores:
            import pdb
            pdb.set_trace()
        assert core in self.cores
        return self.cores[core]*self.height_per_core

    def _scale_time(self, time):
        "Determines scale factor for time"
        return (time + 50) * self.scale_x

    def _scale_cost(self, cost):
        return cost * self.scale_x * .75

    def _scale_height(self, size):
        return size*.4

    def send(self, core, to, time, cost):
        "Visualize send operation"
        name = 's_%s_%s' % (core, to)

        self.f.write("\\node[draw,fill=red!20,minimum width=%fmm, minimum height=%fmm,anchor=west] "\
                         "(%s) at (%fmm,%fmm) {};\n" % \
                         (self._scale_cost(cost), self._scale_height(8), name, \
                              self._scale_time(time), \
                              self._y_coord_for_core(core)))
        self.__add_object(core, name)


    def receive(self, core, sender, time, cost):
        "Visualize receive operation"

        # Box indicating receive operation
        name = 'r_%s_%s' % (sender, core)
        self.f.write("\\node[draw,fill=blue!20,minimum width=%fmm, minimum height=%fmm,anchor=west] "\
                         "(%s) at (%fmm,%fmm) {};\n" % \
                         (self._scale_cost(cost), self._scale_height(8), \
                              name, \
                              self._scale_time(time), \
                              self._y_coord_for_core(core)))
        self.__add_object(core, name)

        # Iteratively add settings for drawing the connection
        settings = [""]
        import numa_model
        if isinstance(self.model, numa_model.NUMAModel):
            if not self.model.on_same_numa_node(core, sender):
                settings.append('semithick')
                settings.append('color=red')
        # Arrow indicating flow
        self.f.write("\\draw[->%s] ($(s_%s_%s.east)-(1mm,0mm)$) -- ($(r_%s_%s.west)+(1mm,0mm)$); \n" % \
                         (','.join(settings), sender, core, sender, core))

    def finalize(self, final_time):
        # header
        self.f.write("\\begin{pgfonlayer}{background}\n")
        # grey background box spanning all objects
        n = [ '(%s)' % x for x in self.obj ]
        # add empty node containing all objects for easier calculation
        self.f.write("\\node [fit=%s] (allobjects) {};\n" % ' '.join(n))
        self.f.write("\\node [draw=black!50,fill=black!10,fit=%s,scale=1.1] (bg) {};\n" % \
                         ' '.join(n))

        # Dummy object to extend NUMA nodes to the right
        for c in self.model.get_graph().nodes():
            numa_name = 'numa_axis_%s' % c
            self.f.write("\\draw let \\p1 = (allobjects.east) in node[] (%s) at (\\x1,%dmm) {};\n" % \
                             (numa_name, self._y_coord_for_core(c)))

        # Are cores "packed" on nodes?
        packed = True
        assert self.model.get_num_numa_nodes()>0 # at least one node
        _cores_on_node = self.model.get_numa_node_by_id(0)
        for i in range(len(_cores_on_node)-1):
            packed = packed and _cores_on_node[i] == _cores_on_node[i]+1
        logging.info(('Visualization: packed display %d' % packed))

        # Individual core by core, no merging of neighboring cores in one box
        if not packed:
            print self.obj_per_core
            for c in self.model.get_cores(True):
                cidx = self.model.get_numa_id(c) % int(len(self.color_map))
                color = self.color_map[cidx]
                self.obj_per_core[c] = self.obj_per_core.get(c, []) + ['numa_axis_%d.west' % (c)]
                nn = [ '(%s)' % x for x in self.obj_per_core[c] ]
                self.f.write("\\node [yscale=0.85,draw=%s!50,fill=%s!10,fit=%s,rounded corners] {};\n" \
                                 % (color, color, ' '.join(nn)))

        # colored background box for each numa domain - merging nodes
        else:
            for i in range(self.model.get_num_numa_nodes()):
                cidx = i % int(len(self.color_map))
                color = self.color_map[cidx]
                coreid = self.model.get_numa_node_by_id(i)[0]

                self.obj_per_node[i].append('numa_axis_%d.west' % (coreid))
                nn = [ '(%s)' % x for x in self.obj_per_node[i] ]
                self.f.write("\\node [yscale=0.85,draw=%s!50,fill=%s!10,fit=%s,rounded corners] {};\n" \
                                 % (color, color, ' '.join(nn)))

        # X-axes
        for c in self.model.get_graph().nodes():
            self.f.write("\\draw[color=black!30] let \\p1 = (core_10_label.east), \\p2 = (allobjects.east) in (\\x1,%dmm) -- (\\x2,%dmm);\n" % \
                             (self._y_coord_for_core(c), self._y_coord_for_core(c)))


        self.f.write("\\node[draw=black,anchor=north,fill=black!20] at (bg.north) {Machine: %s, topology: %s};\n" % (
                self.model.get_name(),
                self.topo.get_name()
                ))

        for xaxis_label in range(0, final_time, 500):
            self.f.write("\\node at (%dmm,-5mm) { %d };\n" % \
                         (self._scale_time(xaxis_label), xaxis_label))

        # footer
        self.f.write("\\end{pgfonlayer}\n")
        self.f.close()


        # Generate a PNG? Currently, this works only for atomic broadcasts
        if config.args.visu and 'atomic_broadcast' in self.name:
            self.__generate_image()


    def __core_label_to_y_index(self):
        return helpers.core_index_dict(self.model.get_graph().nodes())



    def __generate_image(self):

        with open('test.tex', 'w') as f:

            _out = self.name.replace('.tex', '.png')
            print 'Generating visualization .. '

            for line in open('template.tex', 'r'):
                f.write(line.replace('{%file%}', self.name))

            f.close()

            try:
                print subprocess.check_output(shlex.split('rm -f test-figure0.pdf'))
                print subprocess.check_output(shlex.split('pdflatex -shell-escape -interaction nonstopmode test.tex'))
                print subprocess.check_output(shlex.split('convert -verbose -density 300 test-figure0.pdf %s' % _out))

            except Exception as e:
                print 'Generating visualization failed, aborting'
                raise e
