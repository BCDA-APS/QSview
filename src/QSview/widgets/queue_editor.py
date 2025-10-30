"""
Queue Editor Widget - for editing and managing the queue.
"""

from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer

from .. import utils
from .queue_model import QueueTableModel
from .queue_model_dynamic import DynamicQueueTableModel


class QueueEditorWidget(QtWidgets.QWidget):
    """Queue editor widget."""

    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent=None, model=None):
        super().__init__(parent)
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.model = model
        self.setup()

    def setup(self):
        """Connect signals and slots."""
        # Create table model
        self.static_model = QueueTableModel(table_view=self.tableView)
        self.dynamic_model = DynamicQueueTableModel(table_view=self.tableView)

        # Start with static model
        self.current_model = self.dynamic_model
        self.tableView.setModel(self.current_model)

        # # Cap column size
        # MAX = utils.MAX_LENGTH_COLUMN_QUEUE
        # header = self.tableView.horizontalHeader()
        # header.setSectionResizeMode(QHeaderView.Interactive)  # allow user drag-resize
        # header.setMaximumSectionSize(MAX)

        # Checkbox toggle view
        self.viewCheckBox.setChecked(True)
        self.viewCheckBox.setText("Detailed View")

        # Connect to model signals
        self.model.queueChanged.connect(self.static_model.update_data)
        self.model.queueChanged.connect(self.dynamic_model.update_data)
        self.model.queueChanged.connect(self._schedule_resize)
        self.model.queueNeedsUpdate.connect(self._on_queue_needs_update)

        # Connect UI signals
        self.clearButton.clicked.connect(self._on_clear_clicked)
        self.viewCheckBox.stateChanged.connect(self._on_toggle_view)

    def _on_queue_needs_update(self):
        """Handle queue update signal."""
        self.model.fetchQueue()

    def _schedule_resize(self, *_):
        QTimer.singleShot(0, self._resize_table)

    def _on_toggle_view(self):
        """Toggle between static and dynamic view."""
        if self.viewCheckBox.isChecked():
            # Switch to dynamic
            self.current_model = self.dynamic_model
            self.viewCheckBox.setText("Detailed View")
        else:
            # Switch to static
            self.current_model = self.static_model
            self.viewCheckBox.setText("Summary View")

        # Update the table view
        self.tableView.setModel(self.current_model)
        self._resize_table()

    def _on_clear_clicked(self):
        """Clear the queue on the server."""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Clear Queue",
            "Are you sure you want to clear the queue?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        if reply == QtWidgets.QMessageBox.Yes:
            if self.model:
                self.model.clearQueue()
            self.model.messageChanged.emit("Queue cleared")

    def _resize_table(self):
        max_length = (
            utils.MAX_LENGTH_COLUMN_QUEUE_STATIC
            if self.current_model == self.static_model
            else utils.MAX_LENGTH_COLUMN_QUEUE_DYNAMIC
        )
        utils.resize_table_with_caps(self.tableView, max_length)

    def onConnectionChanged(self, is_connected, control_addr, info_addr):
        """Handle connection changes from QueueServerModel signal."""
        if is_connected:
            # Fetch queue when connected
            self.model.fetchQueue()
            QTimer.singleShot(0, self._resize_table)

    def onStatusChanged(self, is_connected, status):
        """Handle periodic status updates from model (every 0.5s)."""
        if status:
            queue_count = status.get("items_in_queue", 0)
            self.itemsQueueLabel.setText(str(queue_count))
