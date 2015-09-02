from hybrid_model import HybridModule
import overlay

class ShmSpmc(HybridModule):
    """
    """

    def __init__(self, sender, receivers, parent):
        super(ShmSpmc, self).__init__(parent)
        self.sender = sender
        self.receivers = receivers

class Shm(overlay.Overlay):
    """Dummy class for shared memory overlays

    """

    def get_name(self):
        return "Shared Memory"
