"""
History Table Model - displays queue history in a table format.
"""

from PyQt5 import QtGui


class HistoryTableModel(QtGui.QStandardItemModel):
    """Table model for displaying queue history with static columns."""

    def __init__(self, parent=None, table_view=None):
        super().__init__(parent)
        self.table_view = table_view
        self.setup_headers()

    def setup_headers(self):
        """Set up table column headers."""
        headers = ["Status", "Name", "Arguments", "User"]
        self.setHorizontalHeaderLabels(headers)

    def update_data(self, history_data):
        """Update table with new history data."""
        # Clear existing data
        self.clear()
        self.setup_headers()

        # Add each history item as a row
        for item_data in history_data:
            row_data = self.extract_row_data(item_data)
            self.add_row(row_data)

        # Resize after data is loaded
        if self.table_view:
            self.table_view.resizeColumnsToContents()
            self.table_view.resizeRowsToContents()

    def extract_row_data(self, history_item):
        """Extract data for a single row from history item."""

        result = history_item.get("result", {})

        return [
            result.get("exit_status", "Unknown"),  # Status
            history_item.get("name", "Unknown"),  # Name
            self.format_arguments(history_item.get("kwargs", {})),  # Arguments
            history_item.get("user", "Unknown"),  # User
        ]

    def add_row(self, row_data):
        """Add a new row to the table."""
        row = self.rowCount()  # Get current number of rows
        self.insertRow(row)  # Insert new row at that position

        # Set data for each column
        for col, data in enumerate(row_data):
            item = QtGui.QStandardItem(str(data))
            self.setItem(row, col, item)

    def format_arguments(self, kwargs):
        """Format arguments for display."""
        if not kwargs:
            return ""

        lines = []
        for key, value in kwargs.items():
            lines.append(f"{key} = {value}")
        return "\n".join(lines)
