# Draw result of evaluation

import numa_model

class Output():

    color_map = [ "red", "green", "blue", "orange" ]
    height_per_core = 15

    "Wrapper to enable visualization output to file"
    def __init__(self, name, model):
        self.name = name
        self.model = model
        self.f = open(name, 'w')
        for i in range(self.model.get_num_cores()):
            # Background
            cidx = int(self.model.get_numa_id(i)) % int(len(self.color_map))
            color = self.color_map[cidx]
            self.f.write("\\draw[fill,color=%s!10] (-3cm,%fmm) rectangle (30cm,%fmm);\n" % \
                             ( \
                    color, 
                    self._y_coord_for_core(i) + (self.height_per_core/2.), \
                    self._y_coord_for_core(i) - (self.height_per_core/2.) \
                    ))
            # Label
            self.f.write("\\node at (0mm,%dmm) {core %02d};\n" % \
                             (self._y_coord_for_core(i), i))
            # y-axis
            self.f.write("\\draw[color=black!30] (20mm,%dmm) -- (30cm,%dmm);\n" % \
                             (self._y_coord_for_core(i), \
                                  self._y_coord_for_core(i)))

    def _y_coord_for_core(self, core):
        "Determines padding between cores"
        return core*self.height_per_core

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
        # Iteratively add settings for drawing the connection
        settings = [""]
        if isinstance(self.model, numa_model.NUMAModel):
            if not self.model.on_same_numa_node(core, sender):
                settings.append('very thick')
        # Arrow indicating flow
        self.f.write("\\draw[->%s] (s_%d_%d.center) -- (r_%d_%d.center); \n" % \
                         (','.join(settings), sender, core, sender, core))
