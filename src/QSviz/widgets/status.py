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
        print(f"Parent: {parent}")  # Debug
        self.mainwindow = parent
        self.setup()

    def setup(self):
        """Setup connections and initialize status."""
        # Connection status
        self.is_connected = False
        self._update_connection_status()

        # Connect signals and slots
        # RE environment buttons
        self.runEngineOpenButton.clicked.connect(self.do_run_engine_open)
        self.runEngineCloseButton.clicked.connect(self.do_run_engine_close)
        self.runEngineDestroyButton.clicked.connect(self.do_run_engine_destroy)

        # Auto-update REM status every 2 seconds
        self.set_rem_state()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.set_rem_state)
        self.timer.timeout.connect(self._update_connection_status)
        self.timer.start(2000)  # 2 seconds

    def _update_connection_status(self):
        """Check if connected to server."""
        try:
            if self.rem_api:
                self.rem_api.status()  # Try to call API
                self.is_connected = True
                self.connectionStatusLabel.setText("ONLINE")
                self.connectionStatusLabel.setStyleSheet("color: green;")
            else:
                self.is_connected = False
                self.connectionStatusLabel.setText("OFFLINE")
                self.connectionStatusLabel.setStyleSheet("color: red;")
        except Exception:
            self.is_connected = False
            self.connectionStatusLabel.setText("OFFLINE")
            self.connectionStatusLabel.setStyleSheet("color: red;")

    def do_run_engine_open(self):
        """Open the Run Engine environment."""
        try:
            if self.RE_state() is None:
                self.mainwindow.setStatus("Opening Run Engine")
                self.rem_api.environment_open()
                self.mainwindow.setStatus("Run Engine opened")
            else:
                self.mainwindow.setStatus("Environment already exists")
        except Exception as e:
            self.mainwindow.setStatus(f"Error opening environment: {e}")

    def do_run_engine_close(self):
        """Close the Run Engine environment."""
        try:
            if self.RE_state() is not None:
                self.mainwindow.setStatus("Closing Run Engine")
                self.rem_api.environment_close()
                self.mainwindow.setStatus("Run Engine closed")
            else:
                self.mainwindow.setStatus("Environment already closed")
        except Exception as e:
            self.mainwindow.setStatus(f"Error closing environment: {e}")

    def do_run_engine_destroy(self):
        """Destroy the Run Engine environment."""
        try:
            if self.RE_state() is not None:
                self.mainwindow.setStatus("Destroying Run Engine")
                self.rem_api.environment_destroy()
                self.mainwindow.setStatus("Run Engine destroyed")
            else:
                self.mainwindow.setStatus("Environment already destroyed")
        except Exception as e:
            self.mainwindow.setStatus(f"Error destroying environment: {e}")

    def set_rem_state(self):
        """Update the status of the RE manager."""
        # Get the state of the RE and RE manager:
        RE_state = self.RE_state()
        REM_state = self.REM_state()
        RE_state = RE_state.upper() if RE_state else "None"
        Manager_state = REM_state.get("manager_state", "None")
        Manager_state = Manager_state.upper() if Manager_state else "None"
        # Get the number of items in the queue and history:
        items_in_queue = REM_state.get("items_in_queue", "None")
        items_in_queue = str(items_in_queue) if items_in_queue else "None"
        items_in_history = REM_state.get("items_in_history", "None")
        items_in_history = str(items_in_history) if items_in_history else "None"
        # Get the plan queue mode:
        plan_queue_mode = REM_state.get("plan_queue_mode", "None")
        loop_mode = plan_queue_mode.get("loop", False)
        loop_mode = "ON" if loop_mode else "OFF"
        # Get the queue stop pending:
        queue_stop_pending = REM_state.get("queue_stop_pending", False)
        queue_stop_pending = "YES" if queue_stop_pending else "NO"
        # Set the labels in the status bar:
        self.managerLabel.setText(Manager_state)
        self.runengineLabel.setText(RE_state)
        self.queueLabel.setText(items_in_queue)
        self.historyLabel.setText(items_in_history)
        self.loopLabel.setText(loop_mode)
        self.stopLabel.setText(queue_stop_pending)

    def REM_state(self):
        """Get the current REM state."""
        return self.rem_api.status()

    def RE_state(self):
        """Get the current RE state."""
        return self.rem_api.status().get("re_state", None)
