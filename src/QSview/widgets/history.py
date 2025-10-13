"""
History Widget - for viewing and managing history.
"""

from PyQt5 import QtWidgets

from .. import utils


class HistoryWidget(QtWidgets.QWidget):
    """History widget."""

    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent=None, model=None):
        super().__init__(parent)
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()
        self.model = model

    def setup(self):
        """Connect signals and slots."""
        # TODO: Add signal/slot connections here
        pass

    def onConnectionChanged(self, is_connected, control_addr, info_addr):
        """Handle connection changes from QueueServerModel signal."""
        # TODO: Add connection-dependent updates here
        pass

    def onStatusChanged(self, is_connected, status):
        """Handle periodic status updates from model (every 2s)."""
        # TODO: Add status-dependent updates here
        pass
