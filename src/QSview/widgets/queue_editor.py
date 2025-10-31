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
        self.duplicateButton.clicked.connect(self._on_copy_to_queue_clicked)
        self.deleteButton.clicked.connect(self._on_delete_clicked)
        self.viewCheckBox.stateChanged.connect(self._on_toggle_view)

        # Checkbox queue mode (loop)
        self.loopBox.setChecked(False)
        self.loopBox.stateChanged.connect(self._on_toggle_loop)

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

    def _on_copy_to_queue_clicked(self):
        """Copy the selected plan(s) to the queue"""
        if not self.model:
            return

        # get selected rows
        selection = self.tableView.selectionModel()
        selected_rows = selection.selectedRows()

        if not selected_rows:
            # No selection - show message
            self.model.messageChanged.emit("Please select plan(s) to duplicate")
            return

        # Get the plan data for selected rows
        queue_data = self.model.getQueue()
        selected_items = []

        for row in selected_rows:
            row_index = row.row()
            if row_index < len(queue_data):
                # Extract the item from queue data
                queue_item = queue_data[row_index]
                selected_items.append(queue_item)

        # Add items directly to queue
        if selected_items:
            self.model.add_items_to_queue(selected_items)

    def _on_delete_clicked(self):
        """Delete the selected plan(s) from the queue"""
        if not self.model:
            return

        # get selected rows
        selection = self.tableView.selectionModel()
        selected_rows = selection.selectedRows()

        if not selected_rows:
            # No selection - show message
            self.model.messageChanged.emit("Please select plan(s) to delete")
            return

        # Get the plan data for selected rows
        queue_data = self.model.getQueue()
        uids_to_delete = []

        for row in selected_rows:
            row_index = row.row()
            if row_index < len(queue_data):
                # Extract the item_uid from queue data
                queue_item = queue_data[row_index]
                item_uid = queue_item.get("item_uid", "")
                if item_uid:
                    uids_to_delete.append(item_uid)

        # Delete items using their UIDs
        if uids_to_delete:
            print(uids_to_delete)
            self.model.delete_items_from_queue(uids_to_delete)

    def _on_toggle_loop(self):
        """Toggle between loop mode on and off."""
        if not self.model:
            return

        if self.loopBox.isChecked():
            self.model.set_queue_mode(loop_mode=True, ignore_failures=True)
        else:
            self.model.set_queue_mode(loop_mode=False, ignore_failures=True)

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
