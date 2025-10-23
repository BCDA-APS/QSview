"""
History Widget - for viewing and managing history.
"""

from PyQt5 import QtWidgets

from .. import utils
from .history_model import HistoryTableModel


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
        self.table_model = HistoryTableModel(table_view=self.tableView)
        self.tableView.setModel(self.table_model)

        # Connect to model signals
        self.model.historyChanged.connect(self.table_model.update_data)
        self.model.historyNeedsUpdate.connect(self._on_history_needs_update)

        # Connect UI signals
        self.clearHistoryButton.clicked.connect(self._on_clear_clicked)

    def _on_clear_clicked(self):
        """Clear the history on the server."""
        if self.model:
            self.model.clearHistory()

    def _on_history_needs_update(self):
        """Handle history update signal."""
        self.model.fetchHistory()

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
