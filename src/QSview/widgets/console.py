"""
Console Widget.
"""

from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal

from .. import utils


class ConsoleWidget(QtWidgets.QWidget):
    """Console widget."""

    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent=None, model=None):
        super().__init__(parent)
        utils.myLoadUi(self.ui_file, baseinstance=self)

        self.model = model
        self._console_thread = None
        self.setup()

    def setup(self):
        """Connect signals and slots."""
        self.consoleClearButton.clicked.connect(self._on_clear_clicked)

    def _on_clear_clicked(self):
        """Clear the console output."""
        self.consoleTextEdit.clear()

    def _start_console_monitoring(self):
        """Start the console monitoring thread."""
        # Don't start if already running
        if self._console_thread is not None:
            return

        # Tell the model to enable console monitoring
        self.model.start_console_output_monitoring()

        # Create the thread
        self._console_thread = ConsoleMonitorThread(self.model)

        # Connect the thread's signal to our handler
        self._console_thread.message_received.connect(self._on_message_received)

        # Start the thread
        self._console_thread.start()

    def _stop_console_monitoring(self):
        """Stop the console monitoring thread."""
        # Nothing to stop if not running
        if self._console_thread is None:
            return

        # Tell the model to disable console monitoring
        self.model.stop_console_output_monitoring()

        # Stop the thread
        self._console_thread.stop()

        # Clean up
        self._console_thread = None

    def _on_message_received(self, result):
        """Handle a new console message from the thread."""
        time, msg = result

        # Only display if there's actual text
        if msg:
            self.consoleTextEdit.appendPlainText(msg.rstrip("\n"))

    def onConnectionChanged(self, is_connected, control_addr, info_addr):
        """Handle connection changes from QueueServerModel signal."""
        if is_connected:
            self._start_console_monitoring()
        else:
            self._stop_console_monitoring()

    def onStatusChanged(self, status):
        """Handle periodic status updates from model (every 2s)."""
        # TODO: Add status-dependent updates here
        pass


class ConsoleMonitorThread(QThread):
    """Background thread that monitors console output from the server."""

    message_received = pyqtSignal(object)  # Emits (time, msg) tuple

    def __init__(self, model):
        super().__init__()
        self.model = model
        self._running = True

    def run(self):
        """This runs the background thread."""
        while self._running:
            # Get next message from the model
            result = self.model.console_monitoring_thread()

            # If there is a message, send it to the widget
            self.message_received.emit(result)

    def stop(self):
        "Stop the thread cleanly" ""
        self._running = False
        self.wait()
