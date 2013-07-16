from hybrid_model import HybridModule

class ShmSpmc(HybridModule):
    """
    """

    def __init__(self, sender, receivers, parent):
        super(ShmSpmc, self).__init__(parent)
        self.sender = sender
        self.receivers = receivers
