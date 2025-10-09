"""
Plan Editor Widget - for editing and managing plans.
"""

from PyQt5 import QtWidgets

from .. import utils


class PlanEditorWidget(QtWidgets.QWidget):
    """Plan editor widget."""

    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent=None, rem_api=None):
        super().__init__(parent)
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()
        self.rem_api = rem_api

    def setup(self):
        """Connect signals and slots."""
        # TODO: Add signal/slot connections here
        pass

    def onConnectionChanged(self, rem_api):
        """Handle connection changes from MainWindow signal."""
        self.rem_api = rem_api
        # TODO: Add connection-dependent updates here
