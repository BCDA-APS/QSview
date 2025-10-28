"""
Console Widget.
"""

from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QIntValidator

from .. import utils


class ConsoleWidget(QtWidgets.QWidget):
    """Console widget."""

    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent=None, model=None):
        super().__init__(parent)
        utils.myLoadUi(self.ui_file, baseinstance=self)

        self.model = model
        self._console_thread = None
        self._autoscroll_enabled = True

        self._max_lines = 1000
        self._max_lines_max = 10000  # Upper limit

        self.setup()

    def setup(self):
        """Connect signals and slots."""
        self.consoleClearButton.clicked.connect(self._on_clear_clicked)
        self.consoleAutoscrollCheckbox.setChecked(True)
        self.consoleAutoscrollCheckbox.stateChanged.connect(self._on_autoscroll_changed)

        # Setup max lines input
        self.consoleMaxLineEdit.setText(str(self._max_lines))
        validator = QIntValidator(1, self._max_lines_max)
        self.consoleMaxLineEdit.setValidator(validator)
        self.consoleMaxLineEdit.editingFinished.connect(self._on_max_lines_changed)

    def _on_clear_clicked(self):
        """Clear the console output."""
        self.consoleTextEdit.clear()

    def _on_autoscroll_changed(self, state):
        """Handle autoscroll checkbox state change."""
        self._autoscroll_enabled = self.consoleAutoscrollCheckbox.isChecked()

    def _on_max_lines_changed(self):
        """Handle max lines input change."""
        text = self.consoleMaxLineEdit.text()

        if text:
            value = int(text)
            # Clamp to valid range (1 to max)
            value = max(1, min(self._max_lines_max, value))

            # Update if we clamped it
            self.consoleMaxLineEdit.setText(str(value))

            # Save and trim
            self._max_lines = value
            self._trim_console_lines()

    def _trim_console_lines(self):
        """Remove old lines if console exceeds max lines."""
        # Get current text
        text = self.consoleTextEdit.toPlainText()

        # Split into lines
        lines = text.split("\n")

        # If over the limit, keep only the last _max_lines
        if len(lines) > self._max_lines:
            # Keep only last _max_lines
            lines = lines[-self._max_lines :]

            # Update the display
            self.consoleTextEdit.setPlainText("\n".join(lines))

            # Restore scroll position if autoscroll enabled
            if self._autoscroll_enabled:
                scrollbar = self.consoleTextEdit.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())

    def _on_message_received(self, result):
        """Handle a new console message from the thread."""
        time, msg = result

        # Only display if there's actual text
        if msg:
            self.consoleTextEdit.appendPlainText(msg.rstrip("\n"))

            # Trim if over max lines
            self._trim_console_lines()

            # Auto-scroll to bottom if enabled
            if self._autoscroll_enabled:
                scrollbar = self.consoleTextEdit.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())

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

    def onConnectionChanged(self, is_connected, control_addr, info_addr):
        """Handle connection changes from QueueServerModel signal."""
        if is_connected:
            self._start_console_monitoring()
        else:
            self._stop_console_monitoring()

    def onStatusChanged(self, is_connected, status):
        """Handle periodic status updates from model (every 0.5s)."""
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
        """Stop the thread cleanly"""
        self._running = False
        self.wait()
