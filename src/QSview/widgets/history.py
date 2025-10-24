"""
History Widget - for viewing and managing history.
"""

from PyQt5 import QtWidgets

from .. import utils
from .history_model import HistoryTableModel
from .history_model_dynamic import DynamicHistoryTableModel


class HistoryWidget(QtWidgets.QWidget):
    """History widget."""

    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent=None, model=None):
        super().__init__(parent)
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.model = model
        self.setup()

    def setup(self):
        """Connect signals and slots."""
        # Create table model
        self.static_model = HistoryTableModel(table_view=self.tableView)
        self.dynamic_model = DynamicHistoryTableModel(table_view=self.tableView)

        # Start with static model
        self.current_model = self.static_model
        self.tableView.setModel(self.current_model)
        self.toggleViewButton.setChecked(False)
        self.toggleViewButton.setText("Detailed View")

        # Connect to model signals
        self.model.historyChanged.connect(self.static_model.update_data)
        self.model.historyChanged.connect(self.dynamic_model.update_data)
        self.model.historyNeedsUpdate.connect(self._on_history_needs_update)

        # Connect UI signals
        self.clearHistoryButton.clicked.connect(self._on_clear_clicked)
        self.copyHistoryButton.clicked.connect(self._on_copy_to_queue_clicked)
        self.toggleViewButton.clicked.connect(self._on_toggle_view)

    def _on_history_needs_update(self):
        """Handle history update signal."""
        self.model.fetchHistory()

    def _on_toggle_view(self):
        """Toggle between static and dynamic view."""
        if self.toggleViewButton.isChecked():
            # Switch to dynamic
            self.current_model = self.dynamic_model
            self.toggleViewButton.setText("Summary View")
        else:
            # Switch to static
            self.current_model = self.static_model
            self.toggleViewButton.setText("Detailed View")

        # Update the table view
        self.tableView.setModel(self.current_model)
        self._resize_table()

    def _on_copy_to_queue_clicked(self):
        """Copy the selected item to the queue"""
        if not self.model:
            return

        # get selected rows
        selection = self.tableView.selectionModel()
        selected_rows = selection.selectedRows()

        if not selected_rows:
            # No selection - show message
            self.model.messageChanged.emit(
                "Please select an history item to copy to queue"
            )

        # Get the history data for selected rows
        history_data = self.model.getHistory()
        selected_items = []

        for row in selected_rows:
            row_index = row.row()
            if row_index < len(history_data):
                # Extract the item from history data
                history_item = history_data[row_index]
                selected_items.append(history_item)

        # Add items directly to queue
        if selected_items:
            self.model.add_items_to_queue(selected_items)

    def _on_clear_clicked(self):
        """Clear the history on the server."""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to clear the history?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        if reply == QtWidgets.QMessageBox.Yes:
            if self.model:
                self.model.clearHistory()
            self.setMessage("History cleared")

    def _resize_table(self):
        """Resize table after data is loaded."""
        self.tableView.resizeColumnsToContents()
        self.tableView.resizeRowsToContents()

    def onConnectionChanged(self, is_connected, control_addr, info_addr):
        """Handle connection changes from QueueServerModel signal."""
        if is_connected:
            # Fetch history when connected
            self.model.fetchHistory()

    def onStatusChanged(self, is_connected, status):
        """Handle periodic status updates from model (every 0.5s)."""
        if status:
            history_count = status.get("items_in_history", 0)
            self.itemsHistoryLabel.setText(str(history_count))
