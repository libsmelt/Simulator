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

