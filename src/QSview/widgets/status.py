"""
Status Widget - displays application status information.
"""

from PyQt5 import QtCore, QtGui, QtWidgets

from .. import (
    resources_rc,  # noqa: F401 - needed to register Qt resources
    utils,
)

# Define the icon constants; see https://stackoverflow.com/questions/38195763/implementing-led-in-pyqt-designer
ICON_RED_LED = ":/icons/led-red-on.png"
ICON_GREEN_LED = ":/icons/green-led-on.png"
ICON_GREY_LED = ":/icons/grey-led-off.png"


class StatusWidget(QtWidgets.QWidget):
    """Status bar widget."""

    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent=None, model=None):
        super().__init__(parent)
        utils.myLoadUi(self.ui_file, baseinstance=self)

        self.mainwindow = parent
        self.model = model

        self._update_RE_status(False, None)
        self._update_REM_status(False, None)
        self._update_Q_status(False, None)
        self._update_QS_status(False, "", "")

        self._connection_lost_dialog_shown = False
        self._has_been_connected = False

        self.setup()

    def setup(self):
        """Setup connections and initialize status."""

        # QS connection button
        self.reconnectButton.clicked.connect(self.do_reconnect)

        # RE environment buttons
        self.runEngineOpenButton.clicked.connect(self.do_RE_open)
        self.runEngineCloseButton.clicked.connect(self.do_RE_close)
        self.runEngineDestroyButton.clicked.connect(self.do_RE_destroy)
        self.runEngineUpdateButton.clicked.connect(self.do_RE_update)

        # Queue control buttons
        self.queueStopButton.setCheckable(True)
        self.queuePlayButton.clicked.connect(self.do_queue_start)
        self.queueStopButton.clicked.connect(self.do_queue_stop_clicked)
        self.autoStartCheckBox.stateChanged.connect(self.do_auto_start)

        # Run Engine control buttons
        self.rePauseButton_deferred.clicked.connect(self.do_RE_pause_deferred)
        self.rePauseButton_immediate.clicked.connect(self.do_RE_pause_immediate)
        self.reResumeButton.clicked.connect(self.do_RE_resume)
        self.reHaltButton.clicked.connect(self.do_RE_halt)
        self.reAbortButton.clicked.connect(self.do_RE_abort)
        self.reStopButton.clicked.connect(self.do_RE_stop)

        # Advanced control
        self.advancedCheckBox.setChecked(False)
        self.advancedCheckBox.stateChanged.connect(self.do_advanced_mode)
        self.rePauseButton_immediate.setVisible(False)
        self.reStopButton.setVisible(False)
        self.reHaltButton.setVisible(False)
        self.runEngineDestroyButton.setVisible(False)
        self.runEngineUpdateButton.setVisible(False)

    # ========================================
    # Connection Control
    # ========================================

    def do_reconnect(self):
        """Attempt to reconnect to the last successful server."""
        if self.model:
            self.model.attemptReconnect()

    # ========================================
    # Queue Control
    # ========================================

    def do_queue_start(self):
        """Start the queue."""
        rem_api = self.model.getREManagerAPI() if self.model else None
        if not rem_api:
            self.mainwindow.setMessage("Not connected to server")
            return
        try:
            success, msg = rem_api.queue_start()
            if not success:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Error",
                    f"Error starting queue: {msg}",
                )
                self.mainwindow.setMessage(f"Error starting queue: {msg}")
            else:
                self.mainwindow.setMessage("Queue started successfully")
        except Exception as e:
            self.mainwindow.setMessage(f"Error starting queue: {e}")

    def do_queue_stop(self):
        """Stop the queue."""
        rem_api = self.model.getREManagerAPI() if self.model else None
        if not rem_api:
            self.mainwindow.setMessage("Not connected to server")
            return
        try:
            success, msg = rem_api.queue_stop()
            if not success:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Error",
                    f"Error stopping queue: {msg}",
                )
                self.mainwindow.setMessage(f"Error stopping queue: {msg}")
            else:
                self.mainwindow.setMessage("Queue stopped successfully")
        except Exception as e:
            self.mainwindow.setMessage(f"Error stopping queue: {e}")

    def do_queue_stop_cancel(self):
        """Cancel pending request to stop the queue."""
        rem_api = self.model.getREManagerAPI() if self.model else None
        if not rem_api:
            self.mainwindow.setMessage("Not connected to server")
            return
        try:
            success, msg = rem_api.queue_stop_cancel()
            if not success:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Error",
                    f"Error cancelling pending request to stop the queue: {msg}",
                )
                self.mainwindow.setMessage(
                    f"Error cancelling pending request to stop the queue: {msg}"
                )
            else:
                self.mainwindow.setMessage(
                    "Successfully cancel the pending request to stop execution of the queue"
                )
        except Exception as e:
            self.mainwindow.setMessage(
                f"Error cancelling pending request to stop the queue: {e}"
            )

    def do_queue_stop_clicked(self):
        """Handle stop button click: stop queue if unchecked, cancel if checked."""
        try:
            if self.queueStopButton.isChecked():
                self.do_queue_stop()
            else:
                self.do_queue_stop_cancel()
        except Exception as ex:
            print(f"Exception: {ex}")

    def do_auto_start(self):
        """Set the auto-start state."""
        rem_api = self.model.getREManagerAPI() if self.model else None
        if not rem_api:
            self.mainwindow.setMessage("Not connected to server")
            return
        try:
            success, msg = rem_api.queue_autostart(self.autoStartCheckBox.isChecked())
            if not success:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Error",
                    f"Error setting auto-start: {msg}",
                )
                self.mainwindow.setMessage(f"Error setting auto-start: {msg}")
            else:
                self.mainwindow.setMessage("Auto-start set successfully")
        except Exception as e:
            self.mainwindow.setMessage(f"Error setting auto-start: {e}")

    # ========================================
    # RE Environment Control (Infrastructure)
    # ========================================

    def do_RE_open(self):
        """Open the Run Engine environment."""
        rem_api, is_connected, re_status = self._get_cached_state()
        if not is_connected:
            self.mainwindow.setMessage("Not connected to server")
            return
        try:
            if re_status is None:
                self.mainwindow.setMessage("Opening Run Engine...")
                success, msg = rem_api.environment_open()
                if not success:
                    QtWidgets.QMessageBox.critical(
                        self,
                        "Error",
                        f"Error opening environment: {msg}",
                    )
                    self.mainwindow.setMessage(f"Error opening environment: {msg}")
                else:
                    self.mainwindow.setMessage("Run Engine opened")
            else:
                self.mainwindow.setMessage("Environment already exists")
        except Exception as e:
            self.mainwindow.setMessage(f"Error opening environment: {e}")

    def do_RE_close(self):
        """Close the Run Engine environment."""
        rem_api, is_connected, re_status = self._get_cached_state()
        if not is_connected:
            self.mainwindow.setMessage("Not connected to server")
            return
        try:
            if re_status is not None:
                self.mainwindow.setMessage("Closing Run Engine...")
                success, msg = rem_api.environment_close()
                if not success:
                    QtWidgets.QMessageBox.critical(
                        self,
                        "Error",
                        f"Error closing environment: {msg}",
                    )
                    self.mainwindow.setMessage(f"Error closing environment: {msg}")
                else:
                    self.mainwindow.setMessage("Run Engine closed")
            else:
                self.mainwindow.setMessage("Environment already closed")
        except Exception as e:
            self.mainwindow.setMessage(f"Error closing environment: {e}")

    def do_RE_destroy(self):
        """Destroy the Run Engine environment."""
        rem_api, is_connected, re_status = self._get_cached_state()
        if not is_connected:
            self.mainwindow.setMessage("Not connected to server")
            return
        try:
            if re_status is not None:
                self.mainwindow.setMessage("Destroying Run Engine...")
                success, msg = rem_api.environment_destroy()
                if not success:
                    QtWidgets.QMessageBox.critical(
                        self,
                        "Error",
                        f"Error destroying environment: {msg}",
                    )
                    self.mainwindow.setMessage(f"Error destroying environment: {msg}")
                else:
                    self.mainwindow.setMessage("Run Engine destroyed")
            else:
                self.mainwindow.setMessage("Environment already destroyed")
        except Exception as e:
            self.mainwindow.setMessage(f"Error destroying environment: {e}")

    def do_RE_update(self):
        """Update the Run Engine environment."""
        rem_api, is_connected, re_status = self._get_cached_state()
        if not is_connected:
            self.mainwindow.setMessage("Not connected to server")
            return
        try:
            if re_status is not None:
                self.mainwindow.setMessage("Updating Run Engine...")
                success, msg, task_uid = rem_api.environment_update()
                if not success:
                    QtWidgets.QMessageBox.critical(
                        self,
                        "Error",
                        f"Error updating environment: {msg}",
                    )
                    self.mainwindow.setMessage(f"Error updating environment: {msg}")
                else:
                    self.mainwindow.setMessage("Run Engine updated")
        except Exception as e:
            self.mainwindow.setMessage(f"Error updating environment: {e}")

    # ========================================
    # RE Execution Control (Run Control)
    # ========================================

    def do_RE_pause_deferred(self):
        """Pause the Run Engine at the next checkpoint (deferred)."""
        rem_api, is_connected, re_status = self._get_cached_state()
        if not is_connected:
            self.mainwindow.setMessage("Not connected to server")
            return
        try:
            success, msg = rem_api.re_pause("deferred")
            if not success:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Error",
                    f"Error pausing Run Engine: {msg}",
                )
                self.mainwindow.setMessage(f"Error pausing Run Engine: {msg}")
            else:
                self.mainwindow.setMessage(
                    "Run Engine will pause at the next checkpoint"
                )
        except Exception as e:
            self.mainwindow.setMessage(f"Error pausing Run Engine: {e}")

    def do_RE_pause_immediate(self):
        """Pause the Run Engine immediately."""
        rem_api, is_connected, re_status = self._get_cached_state()
        if not is_connected:
            self.mainwindow.setMessage("Not connected to server")
            return
        try:
            success, msg = rem_api.re_pause("immediate")
            if not success:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Error",
                    f"Error pausing Run Engine: {msg}",
                )
                self.mainwindow.setMessage(f"Error pausing Run Engine: {msg}")
            else:
                self.mainwindow.setMessage("Run Engine paused immediately")
        except Exception as e:
            self.mainwindow.setMessage(f"Error pausing Run Engine: {e}")

    def do_RE_resume(self):
        """Resume the Run Engine."""
        rem_api, is_connected, re_status = self._get_cached_state()
        if not is_connected:
            self.mainwindow.setMessage("Not connected to server")
            return
        try:
            success, msg = rem_api.re_resume()
            if not success:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Error",
                    f"Error resuming Run Engine: {msg}",
                )
                self.mainwindow.setMessage(f"Error resuming Run Engine: {msg}")
            else:
                self.mainwindow.setMessage("Run Engine resumed")
        except Exception as e:
            self.mainwindow.setMessage(f"Error resuming Run Engine: {e}")

    def do_RE_halt(self):
        """Halt the Run Engine."""
        rem_api, is_connected, re_status = self._get_cached_state()
        if not is_connected:
            self.mainwindow.setMessage("Not connected to server")
            return
        try:
            success, msg = rem_api.re_halt()
            if not success:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Error",
                    f"Error halting Run Engine: {msg}",
                )
                self.mainwindow.setMessage(f"Error halting Run Engine: {msg}")
            else:
                self.mainwindow.setMessage("Run Engine halted")
        except Exception as e:
            self.mainwindow.setMessage(f"Error halting Run Engine: {e}")

    def do_RE_abort(self):
        """Abort the Run Engine."""
        rem_api, is_connected, re_status = self._get_cached_state()
        if not is_connected:
            self.mainwindow.setMessage("Not connected to server")
            return
        try:
            success, msg = rem_api.re_abort()
            if not success:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Error",
                    f"Error aborting Run Engine: {msg}",
                )
                self.mainwindow.setMessage(f"Error aborting Run Engine: {msg}")
            else:
                self.mainwindow.setMessage("Run Engine aborted")
        except Exception as e:
            self.mainwindow.setMessage(f"Error aborting Run Engine: {e}")

    def do_RE_stop(self):
        """Stop the Run Engine."""
        rem_api, is_connected, re_status = self._get_cached_state()
        if not is_connected:
            self.mainwindow.setMessage("Not connected to server")
            return
        try:
            success, msg = rem_api.re_stop()
            if not success:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Error",
                    f"Error stopping Run Engine: {msg}",
                )
                self.mainwindow.setMessage(f"Error stopping Run Engine: {msg}")
            else:
                self.mainwindow.setMessage("Run Engine stopped")
        except Exception as e:
            self.mainwindow.setMessage(f"Error stopping Run Engine: {e}")

    # ========================================
    # Status Update Methods
    # ========================================

    def _update_REM_status(self, is_connected, status):
        """Update the status of the RE manager."""
        labels = [
            self.runengineLabel,
            self.managerLabel,
            # self.loopLabel,
        ]
        if not status:
            # Clear when no status
            for label in labels:
                label.setText("")
            return

        # Format and set labels
        self.managerLabel.setText(str(status.get("manager_state", "NONE")).upper())
        # Handle plan mode (dictionary)
        # plan_mode = status.get("plan_queue_mode", {})
        # self.loopLabel.setText("ON" if plan_mode.get("loop") else "OFF")

    def _update_RE_status(self, is_connected, status):
        """Update UI based on connection state."""
        if not is_connected:
            # Grey LED when no status
            pixmap = QtGui.QPixmap(ICON_GREY_LED)
            self.RELEDLabel.setPixmap(
                pixmap.scaled(
                    20, 20, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
                )
            )
            # Disable RE Environment buttons
            self.runEngineOpenButton.setEnabled(False)
            self.runEngineCloseButton.setEnabled(False)
            self.runEngineDestroyButton.setEnabled(False)
            # Disable RE Control buttons
            self.rePauseButton_deferred.setEnabled(False)
            self.rePauseButton_immediate.setEnabled(False)
            self.reResumeButton.setEnabled(False)
            self.reHaltButton.setEnabled(False)
            self.reAbortButton.setEnabled(False)
            self.reStopButton.setEnabled(False)
            return

        RE_state = status.get("re_state", None)
        manager_state = status.get("manager_state", None)
        worker_exists = status.get("worker_environment_exists", False)

        # Environment controls
        self.runEngineOpenButton.setEnabled(is_connected and not worker_exists)
        self.runEngineUpdateButton.setEnabled(is_connected and worker_exists)
        self.runEngineCloseButton.setEnabled(is_connected and worker_exists)
        self.runEngineDestroyButton.setEnabled(is_connected and worker_exists)

        # Run Engine controls - Pause buttons enabled when running
        is_running = RE_state == "running" or manager_state == "executing_queue"
        is_paused = RE_state == "paused" or manager_state == "paused"

        self.rePauseButton_deferred.setEnabled(
            is_connected and worker_exists and is_running
        )
        self.rePauseButton_immediate.setEnabled(
            is_connected and worker_exists and is_running
        )

        # Resume, Stop, Abort, Halt enabled only when paused
        self.reResumeButton.setEnabled(is_connected and worker_exists and is_paused)
        self.reStopButton.setEnabled(is_connected and worker_exists and is_paused)
        self.reAbortButton.setEnabled(is_connected and worker_exists and is_paused)
        self.reHaltButton.setEnabled(is_connected and worker_exists and is_paused)

        if RE_state is not None:
            pixmap = QtGui.QPixmap(ICON_GREEN_LED)
            self.RELEDLabel.setPixmap(
                pixmap.scaled(
                    20, 20, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
                )
            )
        else:
            pixmap = QtGui.QPixmap(ICON_RED_LED)
            self.RELEDLabel.setPixmap(
                pixmap.scaled(
                    20, 20, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
                )
            )
        self.runengineLabel.setText(str(RE_state or "NONE").upper())

    def _update_QS_status(self, is_connected, control_addr, info_addr):
        """Update UI based on connection state."""

        if is_connected and control_addr and info_addr:
            self.serverAddrLabel.setText(f"{control_addr}")
            pixmap = QtGui.QPixmap(ICON_GREEN_LED)
            self.QSLEDLabel.setPixmap(
                pixmap.scaled(
                    20, 20, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
                )
            )
        else:
            self.serverAddrLabel.setText("No Connection")
            pixmap = QtGui.QPixmap(ICON_RED_LED)
            self.QSLEDLabel.setPixmap(
                pixmap.scaled(
                    20, 20, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
                )
            )

    def _update_Q_status(self, is_connected, status):
        """Update UI based on the queue status"""
        if not is_connected:
            self.queueStatusLabel.setText("")
            self.queueStopButton.setChecked(False)
            # Disable buttons
            self.queuePlayButton.setEnabled(False)
            self.queueStopButton.setEnabled(False)
            return

        worker_exists = status.get("worker_environment_exists", False)
        running_item_uid = status.get("running_item_uid", None)
        queue_stop_pending = status.get("queue_stop_pending", False)
        queue_autostart_enabled = status.get("queue_autostart_enabled", False)

        # Queue controls - Start disabled when running, Stop enabled when running
        is_queue_running = running_item_uid is not None

        if queue_autostart_enabled:
            queue_start_enabled = False
        else:
            queue_start_enabled = (
                is_connected and worker_exists and not is_queue_running
            )

        self.queuePlayButton.setEnabled(queue_start_enabled)
        self.queueStopButton.setEnabled(
            is_connected and worker_exists and is_queue_running
        )

        # Enable auto-start only when worker exists
        self.autoStartCheckBox.setEnabled(is_connected and worker_exists)

        # Update buttons to match server state
        self.queueStopButton.setChecked(queue_stop_pending)
        self.autoStartCheckBox.setChecked(queue_autostart_enabled)

        # Update queue status
        if queue_stop_pending and running_item_uid:
            msg = "STOP PENDING"
        elif running_item_uid:
            msg = "RUNNING"
        else:
            msg = "STOPPED"
        self.queueStatusLabel.setText(msg)

    # ========================================
    # Helper Methods
    # ========================================

    def _get_cached_state(self):
        """Return (rem_api, is_connected, re_state) from model's cached status."""
        if not self.model:
            return None, False, None
        rem_api = self.model.getREManagerAPI()
        is_connected = self.model.isConnected()
        status = self.model.getStatus()
        re_status = status.get("re_state", None) if status else None
        return rem_api, is_connected, re_status

    # ========================================
    # Status & Connection
    # ========================================

    def onStatusChanged(self, is_connected, status):
        """Handle periodic status updates from model (every 0.5s)."""
        self._update_RE_status(is_connected, status)
        self._update_REM_status(is_connected, status)
        self._update_Q_status(is_connected, status)

    def onConnectionChanged(self, is_connected, control_addr, info_addr):
        """Handle connection changes from model signal."""
        self._update_QS_status(
            is_connected, control_addr, info_addr
        )  # no need to change status since onStatusChanged fires right after onConnectionChanged

        # Track successful connections
        if is_connected and control_addr and control_addr != "reconnecting":
            self._has_been_connected = True
            self._connection_lost_dialog_shown = False

        # Show connection lost dialog only for actual disconnections (not reconnecting)
        if (
            not is_connected
            and control_addr != "reconnecting"
            and self._has_been_connected
            and not self._connection_lost_dialog_shown
        ):
            self._connection_lost_dialog_shown = True
            # Use QTimer to show dialog asynchronously to avoid blocking
            QtCore.QTimer.singleShot(100, self._show_connection_lost_dialog)

    def _show_connection_lost_dialog(self):
        """Show connection lost dialog (called asynchronously)."""
        QtWidgets.QMessageBox.critical(
            self,
            "No Connection",
            "Unable to communicate with the server.\n\nPlease check the server/connection and try reconnecting.",
        )

    # ========================================
    # Advanced mode
    # ========================================

    def do_advanced_mode(self):
        """Toggle visibility of advanced buttons."""
        is_advanced = self.advancedCheckBox.isChecked()
        self.rePauseButton_immediate.setVisible(is_advanced)
        self.reStopButton.setVisible(is_advanced)
        self.reHaltButton.setVisible(is_advanced)
        self.runEngineDestroyButton.setVisible(is_advanced)
        self.runEngineUpdateButton.setVisible(is_advanced)
