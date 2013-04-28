# Draw result of evaluation

class Output():
    "Wrapper to enable visualization output to file"
    def __init__(self, name, num_cores):
        self.name = name
        self.f = open(name, 'w')
        for i in range(num_cores):
            self.f.write("\\node at (0mm,%dmm) {core %02d};\n" % \
                             (self._y_coord_for_core(i), i))
            self.f.write("\\draw[color=black!10] (20mm,%dmm) -- (30cm,%dmm);\n" % \
                             (self._y_coord_for_core(i), \
                                  self._y_coord_for_core(i)))

    def _y_coord_for_core(self, core):
        "Determines padding between cores"
        return core*15

    def _scale_time(self, time):
        "Determines scale factor for time"
        return time + 50

    def _scale_cost(self, cost):
        return cost

    def send(self, core, to, time, cost):
        "Visualize send operation"
        self.f.write("\\node[draw,fill=red!20,minimum size=%dmm] "\
                         "(s_%d_%d) at (%dmm,%dmm) {};\n" % \
                         (self._scale_cost(cost), \
                              core, to, \
                              self._scale_time(time), \
                              self._y_coord_for_core(core)))

    def receive(self, core, sender, time, cost):
        "Visualize receive operation"
        # Box indicating receive operation
        self.f.write("\\node[draw,fill=blue!20,minimum size=%dmm] "\
                         "(r_%d_%d) at (%dmm,%dmm) {};\n" % \
                         (self._scale_cost(cost), \
                              sender, core, \
                              self._scale_time(time), \
                              self._y_coord_for_core(core)))
        # Arrow indicating flow
        self.f.write("\\draw[->] (s_%d_%d.center) -- (r_%d_%d.center); \n" % \
                         (sender, core, sender, core))
