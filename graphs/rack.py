import model
import inspect
import algorithms
import helpers

COST_PROPAGATION=300
COST_SEND=150
COST_RECEIVE=150

class Rack(model.Model):

    def __init__(self, serverclass):
        """
        Initialize a rack.

        @param serverclass Class to instantiate

        """
        assert inspect.isclass(serverclass) 
        self.machines = [ serverclass(), serverclass() ]

        g = algorithms.connect_graphs(self.machines[0].get_graph(), 
                                      self.machines[1].get_graph(), 
                                      (0,0), COST_PROPAGATION)
        super(Rack, self).__init__(g)

        helpers.output_graph(g, 'rack')

    def get_name(self):
        return "rack"

    def get_send_cost(self, src, dest):
        m = self.__get_machine_for_edge((src, dest))

        if not m:
            return COST_SEND
        else:
            (machine, src, dest) = m
            return machine.get_send_cost(src, dest)

    def get_receive_cost(self, src, dest):
        m = self.__get_machine_for_edge((src, dest))

        if not m:
            return COST_RECEIVE
        else:
            (machine, src, dest) = m
            return machine.get_receive_cost(src, dest)

    def get_num_cores(self):
        num = 0
        for m in self.machines:
            num += m.get_num_cores()
        return num

    def get_num_numa_nodes(self):
        num = 0
        for m in self.machines:
            num += m.get_num_numa_nodes()
        return num

    def __get_machine_for_edge(self, (src, dest)):
        """
        

        """
        s = src.split('_')
        d = dest.split('_')

        assert len(s)>=2
        assert len(d)>=2

        smachine = int(s[0])
        dmachine = int(d[0])

        if smachine == dmachine:
            return (self.machines[smachine-1], int(s[1]), int(d[1]))

        else:
            return None

    def get_root_node(self):
        return '1_0'

    def get_numa_id(self, core):
        
        s = core.split('_')
        assert len(s)>=2
        m = int(s[0])

        nid = 0
        for i in range(m-1):
            nid += self.machines[i].get_num_numa_nodes()

        nid += self.machines[m-1].get_numa_id(int(s[1]))
        return nid
