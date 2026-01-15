"""
Dynamic History Table Model - displays queue history with dynamic columns.

This model automatically creates columns based on the parameters found in the history data,
similar to the old GUI's approach.
"""

import inspect
from datetime import datetime

from bluesky_queueserver import construct_parameters
from PyQt5 import QtGui


class DynamicHistoryTableModel(QtGui.QStandardItemModel):
    """Dynamic table model for displaying queue history with parameter-based columns."""

    def __init__(self, parent=None, table_view=None, model=None):
        super().__init__(parent)
        self.table_view = table_view
        self.model = model

    def setup_headers(self, history_data):
        """Set up table column headers based on data content."""
        if not history_data:
            self.setHorizontalHeaderLabels(
                ["Status", "Name", "Metadata", "Time start", "Time stop", "User"]
            )
            return

        # Collect all unique parameter names in order of first appearance
        all_params = []  # use list to preserve order
        seen_params = set()  # use set() to remove duplicates
        for item in history_data:
            original_args = item.get("args", [])
            original_kwargs = item.get("kwargs", {})

            # Try to get bound kwargs to find parameter names (like detectors)
            if self.model:
                bound_args, kwargs = self.model.get_bound_item_arguments(item)

                # If binding failed (args not empty), put args into kwargs as "args"
                if bound_args:
                    kwargs = dict(**{"args": bound_args}, **kwargs)
            else:
                kwargs = original_kwargs
                if original_args:
                    kwargs = dict(**{"args": original_args}, **kwargs)

            # Check if "args" column is needed
            if "args" in kwargs and "args" not in seen_params:
                all_params.append("args")
                seen_params.add("args")

            # Use bound kwargs to find parameter names
            for param in kwargs.keys():
                if param not in seen_params:
                    if param != "md":
                        all_params.append(param)
                        seen_params.add(param)

        # Create column headers: fixed columns + dynamic parameters
        headers = (
            ["Status", "Name"]
            + all_params
            + ["Metadata", "Time start", "Time stop", "User"]
        )
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

        time_start = result.get("time_start", "")
        if time_start:
            time_start = datetime.fromtimestamp(time_start).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        time_stop = result.get("time_stop", "")
        if time_stop:
            time_stop = datetime.fromtimestamp(time_stop).strftime("%Y-%m-%d %H:%M:%S")

        # Try to get bound arguments
        plan_name = history_item.get("name", "")
        original_args = history_item.get("args", [])
        original_kwargs = history_item.get("kwargs", {})

        if self.model:
            args, kwargs = self.model.get_bound_item_arguments(history_item)

            # If binding failed (args not empty), put args into kwargs as "args"
            if args:
                kwargs = dict(**{"args": args}, **kwargs)
                args = []  # Clear args since they're now in kwargs
            elif not args and plan_name:
                # Binding succeeded - extract VAR_POSITIONAL from kwargs
                plan_params = self.model.get_allowed_plan_parameters(name=plan_name)
                if plan_params:
                    parameters = construct_parameters(plan_params.get("parameters", {}))
                    for p in parameters:
                        if p.kind == inspect.Parameter.VAR_POSITIONAL:
                            var_pos_value = kwargs.get(p.name)
                            if var_pos_value is not None:
                                args = (
                                    var_pos_value
                                    if isinstance(var_pos_value, (list, tuple))
                                    else [var_pos_value]
                                )
                                kwargs = kwargs.copy()
                                kwargs.pop(p.name, None)
                            break
        else:
            args = original_args
            kwargs = original_kwargs
            if args:
                kwargs = dict(**{"args": args}, **kwargs)
                args = []

        headers = [
            self.horizontalHeaderItem(i).text() for i in range(self.columnCount())
        ]

        # Add parameter values; skip Status, Name (first 2 columns), Metadata, start/stop time and User (last 4)
        for header in headers[2:-4]:
            if header == "args":
                value = args if args else ""
            else:
                value = kwargs.get(header, "")
            row_data.append(str(value) if value != "" else "")

        # Add metadata, time and user
        row_data.append(kwargs.get("md", ""))
        row_data.append(time_start)
        row_data.append(time_stop)
        row_data.append(history_item.get("user", "Unknown"))

        return row_data

    def add_row(self, row_data):
        """Add a new row to the table."""
        row = self.rowCount()
        self.insertRow(row)

        for col, data in enumerate(row_data):
            item = QtGui.QStandardItem(str(data))
            header = self.horizontalHeaderItem(col).text()
            if header == "Metadata":
                item.setToolTip(str(data))
            self.setItem(row, col, item)
