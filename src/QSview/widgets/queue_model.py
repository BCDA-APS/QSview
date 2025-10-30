"""
Queue Table Model - displays queue items in a table format.
"""

from PyQt5 import QtGui

from ..utils import format_kwargs_three_lines


class QueueTableModel(QtGui.QStandardItemModel):
    """Table model for displaying queue items with static columns."""

    def __init__(self, parent=None, table_view=None):
        super().__init__(parent)
        self.table_view = table_view
        self.setup_headers()

    def setup_headers(self):
        """Set up table column headers."""
        headers = ["Name", "Arguments", "User"]
        self.setHorizontalHeaderLabels(headers)

    def update_data(self, queue_data):
        """Update table with new queue data."""
        # Clear existing data
        self.clear()
        self.setup_headers()

        # Add each queue item as a row
        for item_data in queue_data:
            row_data = self.extract_row_data(item_data)
            self.add_row(row_data)

        # Resize after data is loaded
        if self.table_view:
            self.table_view.resizeColumnsToContents()
            self.table_view.resizeRowsToContents()

    def extract_row_data(self, queue_item):
        """Extract data for a single row from queue item."""

        return [
            queue_item.get("name", "Unknown"),  # Name
            self.format_arguments(queue_item.get("kwargs", {})),  # Arguments
            queue_item.get("user", "Unknown"),  # User
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
        return format_kwargs_three_lines(kwargs)
