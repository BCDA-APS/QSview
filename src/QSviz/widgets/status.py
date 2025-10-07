"""
Status Widget - displays application status information.
"""

from PyQt5 import QtWidgets

from .. import utils


class StatusWidget(QtWidgets.QWidget):
    """Status bar widget."""

    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent=None):
        super().__init__(parent)
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        """Connect signals and slots."""
        # TODO: Add signal/slot connections here
        pass
