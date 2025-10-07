"""
History Widget - for viewing and managing history.
"""

from PyQt5 import QtWidgets

from .. import utils


class HistoryWidget(QtWidgets.QWidget):
    """History widget."""

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
