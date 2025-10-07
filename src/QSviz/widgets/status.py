"""
Status Widget - displays application status information.
"""

from PyQt5 import QtWidgets

from .. import utils


class StatusWidget(QtWidgets.QWidget):
    """Status bar widget."""

    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent=None, rm_api=None):
        super().__init__(parent)
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.rm_api = rm_api
        self.setup()
        self.update_rm_status()

    def setup(self):
        """Connect signals and slots."""
        # TODO: Add signal/slot connections here
        pass

    def update_rm_status(self):
        """Update the status of the REManager API."""
        status = self.rm_api.status()
        RE_state = status.get("re_state", "None")
        self.runengineLabel.setText(RE_state)
