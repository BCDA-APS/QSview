"""
Queue Editor Widget - for editing and managing the queue.
"""

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QTimer

from .. import utils
from .queue_button_delegate import ButtonDelegate
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

        # Install event filter to handle ESC key for deselection
        self.tableView.installEventFilter(self)

        # Checkbox toggle view
        self.viewCheckBox.setChecked(True)
        self.viewCheckBox.setText("Detailed View")

        # Connect to model signals
        self.model.queueChanged.connect(self._on_queue_changed)
        self.model.queueNeedsUpdate.connect(self._on_queue_needs_update)

        # Connect UI signals
        self.clearButton.clicked.connect(self._on_clear_clicked)
        self.duplicateButton.clicked.connect(self._on_copy_to_queue_clicked)
        self.deleteButton.clicked.connect(self._on_delete_clicked)
        self.viewCheckBox.stateChanged.connect(self._on_toggle_view)

        # Populate modeComboBox
        self.modeComboBox.addItems(["Default Mode", "Loop Mode", "Loop Until Failure"])
        self.modeComboBox.currentTextChanged.connect(self._on_mode_changed)

    def _on_queue_changed(self, queue_data):
        """Handle queue changed signal"""

        # Save current scroll positions
        # vsb = self.tableView.verticalScrollBar()
        # hsb = self.tableView.horizontalScrollBar()
        # v = vsb.value()
        # h = hsb.value()

        # Update model
        self.current_model.update_data(queue_data)

        # Schedule resize, delegate and restore scroll position
        QTimer.singleShot(0, self._resize_table)
        QTimer.singleShot(10, self._setup_delegates)
        # TODO: fix scroll bar flickering
        # QTimer.singleShot(20, lambda: self._restore_scroll_position(v, h))

    def _on_queue_needs_update(self):
        """Handle queue update signal."""
        self.model.fetchQueue()

    def _setup_delegates(self):
        """Set up button delegates for Edit/Delete columns."""
        model = self.current_model
        if model.columnCount() < 2:  # Need at least Edit and Delete columns
            return

        # Clear ALL column delegates first (important when switching models)
        for col in range(
            self.tableView.model().columnCount() if self.tableView.model() else 0
        ):
            self.tableView.setItemDelegateForColumn(col, None)

        edit_col = model.columnCount() - 2
        delete_col = model.columnCount() - 1

        # Then create new ones
        edit_delegate = ButtonDelegate(self)
        edit_delegate.button_clicked.connect(self._on_delegate_button_clicked)
        self.tableView.setItemDelegateForColumn(edit_col, edit_delegate)

        delete_delegate = ButtonDelegate(self)
        delete_delegate.button_clicked.connect(self._on_delegate_button_clicked)
        self.tableView.setItemDelegateForColumn(delete_col, delete_delegate)

    def _on_delegate_button_clicked(self, row, is_edit):
        """Handle button click from delegate."""
        if is_edit:
            self._on_edit_cell_clicked(row)
        else:
            self._on_delete_cell_clicked(row)

    def _on_toggle_view(self):
        """Toggle between static and dynamic view."""
        # Get current queue data before switching
        queue_data = self.model.getQueue() if self.model else []
        if self.viewCheckBox.isChecked():
            # Switch to dynamic
            self.current_model = self.dynamic_model
            self.viewCheckBox.setText("Detailed View")
            self.dynamic_model.update_data(queue_data)
        else:
            # Switch to static
            self.current_model = self.static_model
            self.viewCheckBox.setText("Summary View")
            self.static_model.update_data(queue_data)

        # Update the table view
        self.tableView.setModel(self.current_model)
        self._resize_table()
        self._setup_delegates()

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

    def _on_mode_changed(self, text):
        """Change queue execution mode."""
        if not self.model:
            return

        if text == "Default Mode":
            self.model.set_queue_mode(loop_mode="default")
        elif text == "Loop Mode":
            self.model.set_queue_mode(loop_mode=True, ignore_failures=True)
        elif text == "Loop Until Failure":
            self.model.set_queue_mode(loop_mode=True, ignore_failures=False)

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

    def _on_edit_cell_clicked(self, row):
        """Handle Edit button click for a specific row."""
        queue_data = self.model.getQueue()
        if row < len(queue_data):
            queue_item = queue_data[row]
            print(f"Edit clicked for row {row}: {queue_item.get('name')}")
            # TODO: Edit logic goes here

    def _on_delete_cell_clicked(self, row):
        """Handle Delete button click for a specific row."""
        queue_data = self.model.getQueue()
        if row < len(queue_data):
            queue_item = queue_data[row]
            item_uid = queue_item.get("item_uid")
            if item_uid:
                self.model.delete_items_from_queue([item_uid])

    def _resize_table(self):
        """Resize table columns based on current model view type."""
        max_length = (
            utils.MAX_LENGTH_COLUMN_QUEUE_STATIC
            if self.current_model == self.static_model
            else utils.MAX_LENGTH_COLUMN_QUEUE_DYNAMIC
        )
        utils.resize_table_with_caps(self.tableView, max_length)

    def _restore_scroll_position(self, v, h):
        """Restore vertical and horizontal scroll positions after table update."""
        vsb = self.tableView.verticalScrollBar()
        hsb = self.tableView.horizontalScrollBar()
        vsb.setValue(min(v, vsb.maximum()))
        hsb.setValue(min(h, hsb.maximum()))

    def eventFilter(self, obj, event):
        """Handle ESC key to deselect rows in table view."""
        if obj == self.tableView and event.type() == QtCore.QEvent.KeyPress:
            if event.key() == QtCore.Qt.Key_Escape:
                self.tableView.clearSelection()
                return True
        return super().eventFilter(obj, event)

    def onConnectionChanged(self, is_connected, control_addr, info_addr):
        """Handle connection changes from QueueServerModel signal."""
        if is_connected:
            # Fetch queue when connected
            self.model.fetchQueue()
            QTimer.singleShot(0, self._resize_table)
            QTimer.singleShot(10, self._setup_delegates)
            # Handle plan mode at connection
            self.modeComboBox.blockSignals(True)
            try:
                status = self.model.getStatus()
                plan_mode = status.get("plan_queue_mode", {})
                loop = plan_mode.get("loop", False)
                ignore_failures = plan_mode.get("ignore_failures", False)
                if loop and ignore_failures:
                    self.modeComboBox.setCurrentIndex(1)
                elif loop and not ignore_failures:
                    self.modeComboBox.setCurrentIndex(2)
                else:
                    self.modeComboBox.setCurrentIndex(0)
            finally:
                self.modeComboBox.blockSignals(False)

    def onStatusChanged(self, is_connected, status):
        """Handle periodic status updates from model (every 0.5s)."""
        if status:
            queue_count = status.get("items_in_queue", 0)
            self.itemsQueueLabel.setText(str(queue_count))
