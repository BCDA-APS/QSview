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
        self.is_connected = False
        self._update_connection_status()
        self._update_rem_status()
        self.setup()

    def setup(self):
        """Setup connections and initialize status."""

        # Connect/Disconnect buttons
        self.connectButton.clicked.connect(self.mainwindow.connect_to_server)
        self.disconnectButton.clicked.connect(self.mainwindow.disconnect_from_server)

        # RE environment buttons
        self.runEngineOpenButton.clicked.connect(self.do_run_engine_open)
        self.runEngineCloseButton.clicked.connect(self.do_run_engine_close)
        self.runEngineDestroyButton.clicked.connect(self.do_run_engine_destroy)

        # Queue control buttons
        self.queuePlayButton.clicked.connect(self.do_queue_start)
        self.queueStopButton.clicked.connect(self.do_queue_stop)
        self.autoStartCheckBox.stateChanged.connect(self.do_auto_start)

        # Auto-update REM status every 2 seconds
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._update_rem_status)
        self.timer.start(2000)  # 2 seconds

    def REM_state(self):
        """Get the current REM state."""
        try:
            return self.rem_api.status()
        except Exception:
            return None

    def RE_state(self):
        """Get the current RE state."""
        try:
            return self.rem_api.status().get("re_state", None)
        except Exception:
            return None

    def _update_connection_status(self):
        """Update UI based on connection state."""
        if self.is_connected and self.rem_api:
            self.connectionStatusLabel.setText("ONLINE")
            self.connectionStatusLabel.setStyleSheet("color: green;")
        else:
            self.connectionStatusLabel.setText("OFFLINE")
            self.connectionStatusLabel.setStyleSheet("color: red;")

    def do_queue_start(self):
        """Start the queue."""
        self.rem_api.queue_start()

    def do_queue_stop(self):
        """Stop the queue."""
        self.rem_api.queue_stop()

    def do_auto_start(self):
        """Set the auto-start state."""
        self.rem_api.queue_autostart(self.autoStartCheckBox.isChecked())

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

    def _update_rem_status(self):
        """Update the status of the RE manager."""
        labels = [
            self.runengineLabel,
            self.managerLabel,
            self.queueLabel,
            self.historyLabel,
            self.loopLabel,
            self.stopLabel,
        ]

        if not self.rem_api:
            # Clear all labels when disconnected
            for label in labels:
                label.setText("")
            return

        RE_state = self.RE_state()
        REM_state = self.REM_state() or {}

        # Format and set labels
        self.runengineLabel.setText(str(RE_state or "NONE").upper())
        self.managerLabel.setText(str(REM_state.get("manager_state", "NONE")).upper())
        self.queueLabel.setText(str(REM_state.get("items_in_queue", 0)))
        self.historyLabel.setText(str(REM_state.get("items_in_history", 0)))

        # Handle plan mode (dictionary)
        plan_mode = REM_state.get("plan_queue_mode", {})
        self.loopLabel.setText("ON" if plan_mode.get("loop") else "OFF")
        self.stopLabel.setText("YES" if REM_state.get("queue_stop_pending") else "NO")
