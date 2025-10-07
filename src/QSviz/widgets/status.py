"""
Status Widget - displays application status information.
"""

from PyQt5 import QtWidgets, QtCore

from .. import utils


class StatusWidget(QtWidgets.QWidget):
    """Status bar widget."""

    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent=None, rm_api=None):
        super().__init__(parent)
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.rm_api = rm_api
        self.setup()
        self.update_re_status()

        # Auto-update every 2 seconds
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_re_status)
        self.timer.timeout.connect(self.update_rem_status)
        self.timer.start(2000)  # 2 seconds

    def setup(self):
        """Connect signals and slots."""
        # TODO: Add signal/slot connections here
        pass

    def update_re_status(self):
        """Update the status of the RE."""
        status = self.rm_api.status()
        RE_state = status.get("re_state", "None")
        self.runengineLabel.setText(RE_state.upper())

    def update_rem_status(self):
        """Update the status of the RE manager."""
        status = self.rm_api.status()
        REM_state = status.get("manager_state", "None")
        self.managerLabel.setText(REM_state.upper())
