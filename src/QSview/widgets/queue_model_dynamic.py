"""
Dynamic Queue Table Model - displays queue items with dynamic columns.

This model automatically creates columns based on the parameters found in the queue data,
similar to the old GUI's approach.
"""

from PyQt5 import QtGui


class DynamicQueueTableModel(QtGui.QStandardItemModel):
    """Dynamic table model for displaying queue items with parameter-based columns."""

    def __init__(self, parent=None, table_view=None):
        super().__init__(parent)
        self.table_view = table_view

    def setup_headers(self, queue_data):
        """Set up table column headers based on data content."""
        if not queue_data:
            self.setHorizontalHeaderLabels(["Name", "User", "Edit", "Delete"])
            return

        # Collect all unique parameter names in order of first appearance
        all_params = []  # use list to preserve order
        seen_params = set()  # use set() to remove duplicates
        for item in queue_data:
            kwargs = item.get("kwargs", {})
            for param in kwargs.keys():
                if param not in seen_params:
                    all_params.append(param)
                    seen_params.add(param)

        # Create column headers: fixed columns + dynamic parameters
        headers = ["Name"] + all_params + ["User", "Edit", "Delete"]
        self.setHorizontalHeaderLabels(headers)

    def update_data(self, queue_data):
        """Update table with new queue data."""
        self.clear()
        self.setup_headers(queue_data)

        for item_data in queue_data:
            row_data = self.extract_row_data(item_data)
            self.add_row(row_data)

        # Resize after data is loaded
        if self.table_view:
            self.table_view.resizeColumnsToContents()
            self.table_view.resizeRowsToContents()

    def extract_row_data(self, queue_item):
        """Extract data for a single row from queue item."""

        # Start with fixed columns
        row_data = [
            queue_item.get("name", "Unknown"),  # Name
        ]

        # Add dynamic parameter columns
        kwargs = queue_item.get("kwargs", {})
        headers = [
            self.horizontalHeaderItem(i).text() for i in range(self.columnCount())
        ]

        # Add parameter values (skip Name, and User)
        for header in headers[1:-3]:
            value = kwargs.get(header, "")
            row_data.append(str(value) if value != "" else "")

        # Add User last
        row_data.append(queue_item.get("user", "Unknown"))

        return row_data

    def add_row(self, row_data):
        """Add a new row to the table."""
        row = self.rowCount()
        self.insertRow(row)

        for col, data in enumerate(row_data):
            item = QtGui.QStandardItem(str(data))
            self.setItem(row, col, item)
