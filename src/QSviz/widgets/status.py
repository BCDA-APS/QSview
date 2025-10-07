"""
Status Widget - displays application status information.
"""

from PyQt5 import QtCore, QtWidgets

from .. import utils


class StatusWidget(QtWidgets.QWidget):
    """Status bar widget."""

    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent=None, rem_api=None):
        super().__init__(parent)
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.rem_api = rem_api
        self.setup()
        self.get_rem_state()

        # Auto-update every 2 seconds
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.get_rem_state)
        self.timer.start(2000)  # 2 seconds

    def setup(self):
        """Connect signals and slots."""
        # TODO: Add signal/slot connections here
        pass

    def get_rem_state(self):
        """Update the status of the RE manager."""
        self.rem_state = self.rem_api.status()
        # Get the state of the RE manager:
        REM_state = self.rem_state.get("manager_state", "None")
        RE_state = self.rem_state.get("re_state", "None")
        # Get the number of items in the queue and history:
        items_in_queue = self.rem_state.get("items_in_queue", "None")
        items_in_history = self.rem_state.get("items_in_history", "None")
        # Get the plan queue mode:
        plan_queue_mode = self.rem_state.get("plan_queue_mode", "None")
        loop_mode = plan_queue_mode.get("loop", False)
        loop_mode = "ON" if loop_mode else "OFF"
        # Get the queue stop pending:
        queue_stop_pending = self.rem_state.get("queue_stop_pending", False)
        queue_stop_pending = "YES" if queue_stop_pending else "NO"
        # Set the labels in the status bar:
        self.managerLabel.setText(REM_state.upper())
        self.runengineLabel.setText(RE_state.upper())
        self.queueLabel.setText(str(items_in_queue))
        self.historyLabel.setText(str(items_in_history))
        self.loopLabel.setText(loop_mode)
        self.stopLabel.setText(queue_stop_pending)
        return self.rem_state
