"""
Dynamic History Table Model - displays queue history with dynamic columns.

This model automatically creates columns based on the parameters found in the history data,
similar to the old GUI's approach.
"""

from PyQt5 import QtGui


class DynamicHistoryTableModel(QtGui.QStandardItemModel):
    """Dynamic table model for displaying queue history with parameter-based columns."""

    def __init__(self, parent=None, table_view=None):
        super().__init__(parent)
        self.table_view = table_view

    def setup_headers(self, history_data):
        """Set up table column headers based on data content."""
        if not history_data:
            self.setHorizontalHeaderLabels(["Status", "Name", "Metadata", "User"])
            return

        # Collect all unique parameter names in order of first appearance
        all_params = []  # use list to preserve order
        seen_params = set()  # use set() to remove duplicates
        for item in history_data:
            kwargs = item.get("kwargs", {})
            for param in kwargs.keys():
                if param not in seen_params:
                    if param != "md":
                        all_params.append(param)
                        seen_params.add(param)

        # Create column headers: fixed columns + dynamic parameters
        headers = ["Status", "Name"] + all_params + ["Metadata", "User"]
        self.setHorizontalHeaderLabels(headers)

    def update_data(self, history_data):
        """Update table with new history data."""
        self.clear()
        self.setup_headers(history_data)

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

        # Start with fixed columns
        row_data = [
            result.get("exit_status", "Unknown"),  # Status
            history_item.get("name", "Unknown"),  # Name
        ]

        # Add dynamic parameter columns
        kwargs = history_item.get("kwargs", {})
        headers = [
            self.horizontalHeaderItem(i).text() for i in range(self.columnCount())
        ]

        # Add parameter values; skip Status, Name (first 2 columns), Metadata and User (last 2)
        for header in headers[2:-2]:
            value = kwargs.get(header, "")
            row_data.append(str(value) if value != "" else "")

        # Add metadata
        row_data.append(kwargs.get("md", ""))

        # Add User last
        row_data.append(history_item.get("user", "Unknown"))

        return row_data

    def add_row(self, row_data):
        """Add a new row to the table."""
        row = self.rowCount()
        self.insertRow(row)

        for col, data in enumerate(row_data):
            item = QtGui.QStandardItem(str(data))
            self.setItem(row, col, item)
