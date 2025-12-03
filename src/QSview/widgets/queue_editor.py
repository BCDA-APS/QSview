"""
Queue Editor Widget - for editing and managing the queue.
"""

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QTimer

from .. import utils
from .plan_editor import PlanEditorDialog
from .queue_button_delegate import ButtonDelegate
from .queue_model import QueueTableModel
from .queue_model_dynamic import DynamicQueueTableModel


class QueueEditorWidget(QtWidgets.QWidget):
    """Queue editor widget."""

    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent=None, model=None):
        super().__init__(parent)
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.tableView.set_helpers(
            get_uid_for_row=self._get_uid_for_row,
            move_items=self._move_items,
        )
        self.model = model
        self._plan_editor_dialog = None
        self.setup()

    def setup(self):
        """Connect signals and slots."""
        # Create table model
        self.static_model = QueueTableModel(table_view=self.tableView)
        self.dynamic_model = DynamicQueueTableModel(table_view=self.tableView)

        # Start with static model
        self.current_model = self.dynamic_model
        self.tableView.setModel(self.current_model)

        # Ensure table allows multiple row selection (ExtendedSelection allows non-contiguous)
        self.tableView.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        # selectionBehavior is already set to SelectRows in UI file

        # Install event filter to handle ESC key for deselection
        self.tableView.installEventFilter(self)

        # Checkbox toggle view
        self.viewCheckBox.setChecked(True)
        self.viewCheckBox.setText("Detailed View")

        # Connect to model signals
        self.model.queueChanged.connect(self._on_queue_changed)
        self.model.queueNeedsUpdate.connect(self._on_queue_needs_update)
        self.model.queueSelectionChanged.connect(self._apply_selection_from_model)

        # Connect UI signals
        self.clearButton.clicked.connect(self._on_clear_clicked)
        self.duplicateButton.clicked.connect(self._on_copy_to_queue_clicked)
        self.deleteButton.clicked.connect(self._on_delete_clicked)
        self.viewCheckBox.stateChanged.connect(self._on_toggle_view)
        self.topButton.clicked.connect(self._on_top_clicked)
        self.upButton.clicked.connect(self._on_up_clicked)
        self.downButton.clicked.connect(self._on_down_clicked)
        self.bottomButton.clicked.connect(self._on_bottom_clicked)
        self.addQueueButton.clicked.connect(self._on_add_new_plan_clicked)

        # Populate modeComboBox
        self.modeComboBox.addItems(["Default Mode", "Loop Mode", "Loop Until Failure"])
        self.modeComboBox.currentTextChanged.connect(self._on_mode_changed)

        # Clear selection
        self.model.selected_queue_item_uids = []
        self.tableView.clearSelection()

    def _on_queue_changed(self, queue_data):
        """Handle queue change signal"""
        self.current_model.update_data(queue_data)
        QTimer.singleShot(0, self._resize_table)
        QTimer.singleShot(10, self._setup_delegates)

    def _on_queue_needs_update(self):
        """Handle queue update signal."""
        self.model.fetchQueue()

    # =====================================
    # Model Switching & Delegates
    # =====================================

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
        # Ensure selection mode is maintained when switching models
        self.tableView.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self._resize_table()
        self._setup_delegates()

    # =====================================
    # Toolbar Actions
    # =====================================

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

    def _on_add_new_plan_clicked(self):
        """Open plan editor dialog for creating a new plan."""
        # Always destroy existing dialog if it exists and create a new one
        if self._plan_editor_dialog is not None:
            self._plan_editor_dialog.close()
            self._plan_editor_dialog = None

        # Create new dialog
        self._plan_editor_dialog = PlanEditorDialog(parent=self, model=self.model)
        self._plan_editor_dialog.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self._plan_editor_dialog.destroyed.connect(self._on_plan_editor_destroyed)
        self._plan_editor_dialog.show()

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

            if queue_item.get("item_type") != "plan":
                self.model.messageChanged.emit("Can only edit plans, not instructions")
                return

            if self._plan_editor_dialog is None:
                # Create new dialog
                self._plan_editor_dialog = PlanEditorDialog(
                    parent=self, model=self.model
                )
                self._plan_editor_dialog.setAttribute(QtCore.Qt.WA_DeleteOnClose)
                self._plan_editor_dialog.destroyed.connect(
                    self._on_plan_editor_destroyed
                )
                self._plan_editor_dialog.show()

            # Load the item (whether new or existing dialog)
            self._plan_editor_dialog.open_for_editing(queue_item)

            # Bring to front
            self._plan_editor_dialog.raise_()
            self._plan_editor_dialog.activateWindow()

    def _on_plan_editor_destroyed(self):
        """Handle plan editor dialog being destroyed."""
        self._plan_editor_dialog = None

    def _on_delete_cell_clicked(self, row):
        """Handle Delete button click for a specific row."""
        queue_data = self.model.getQueue()
        if row < len(queue_data):
            queue_item = queue_data[row]
            item_uid = queue_item.get("item_uid")
            if item_uid:
                self.model.delete_items_from_queue([item_uid])

    # =====================================
    # Drag and Reorder Items
    # =====================================

    def _on_top_clicked(self):
        """Handle top button clicked"""
        uids, *_ = self._get_uids_for_selection()
        if not uids:
            return
        self.model.selected_queue_item_uids = uids
        self._move_items(uids=uids, pos_dest="front", reorder=True)

    def _on_up_clicked(self):
        """Handle up button clicked"""
        uids, before_uid, _ = self._get_uids_for_selection()
        if not uids or not before_uid:
            return
        self.model.selected_queue_item_uids = uids
        self._move_items(uids=uids, before_uid=before_uid, reorder=True)

    def _on_down_clicked(self):
        """Handle down button clicked"""
        uids, _, after_uid = self._get_uids_for_selection()
        if not uids or not after_uid:
            return
        self.model.selected_queue_item_uids = uids
        self._move_items(uids=uids, after_uid=after_uid, reorder=True)

    def _on_bottom_clicked(self):
        """Handle bottom button clicked"""
        uids, *_ = self._get_uids_for_selection()
        if not uids:
            return
        self.model.selected_queue_item_uids = uids
        self._move_items(uids=uids, pos_dest="back", reorder=True)

    def _get_uid_for_row(self, row):
        queue_data = self.model.getQueue()
        if 0 <= row < len(queue_data):
            return queue_data[row].get("item_uid")
        return None

    def _move_items(self, **kwargs):
        if not self.model:
            return False
        return self.model.move_queue_items(**kwargs)

    def _get_uids_for_selection(self):
        """Return the list of uids for the selected rows"""
        table = getattr(self, "tableView", None)
        if table is None:
            return [], None, None
        selection = table.selectionModel()
        if not selection:
            return [], None, None
        rows = [index.row() for index in selection.selectedRows()]
        uids = []
        for row in rows:
            uid = self._get_uid_for_row(row)
            if uid:
                uids.append(uid)
        if not uids:
            return [], None, None
        before_row = rows[0] - 1
        after_row = rows[-1] + 1
        before_uid = self._get_uid_for_row(before_row) if before_row >= 0 else None
        after_uid = self._get_uid_for_row(after_row)
        return uids, before_uid, after_uid

    @QtCore.pyqtSlot(list)
    def _apply_selection_from_model(self, uids):
        """Restore selection based on UIDs from model (like old GUI approach)."""
        table = getattr(self, "tableView", None)
        if table is None:
            return
        qt_model = table.model()
        selection_model = table.selectionModel()
        if qt_model is None or selection_model is None:
            return

        if not uids:
            # No UIDs to select, just clear selection
            selection_model.clearSelection()
            return

        # Block signals during selection restoration (like old GUI blocks selection processing)
        selection_model.blockSignals(True)
        try:
            # Clear existing selection
            selection_model.clearSelection()

            # Map UIDs to row indices
            queue_data = self.model.getQueue()
            uid_to_row = {
                item.get("item_uid"): row for row, item in enumerate(queue_data)
            }

            # Find valid rows for the UIDs
            rows = []
            for uid in uids:
                row = uid_to_row.get(uid)
                if row is not None:
                    rows.append(row)

            if not rows:
                # No valid rows found
                return

            # Set current index to last row FIRST (like old GUI sets current cell first)
            # Use NoUpdate flag to prevent it from affecting selection
            last_row = rows[-1]
            current_idx = qt_model.index(last_row, 0)
            selection_model.setCurrentIndex(
                current_idx,
                QtCore.QItemSelectionModel.Current
                | QtCore.QItemSelectionModel.NoUpdate,
            )

            # Now build selection for all rows
            selection = QtCore.QItemSelection()
            for row in rows:
                top_left = qt_model.index(row, 0)
                bottom_right = qt_model.index(row, qt_model.columnCount() - 1)
                selection.merge(
                    QtCore.QItemSelection(top_left, bottom_right),
                    QtCore.QItemSelectionModel.Select,
                )

            # Apply selection with ClearAndSelect | Rows
            if not selection.isEmpty():
                selection_model.select(
                    selection,
                    QtCore.QItemSelectionModel.ClearAndSelect
                    | QtCore.QItemSelectionModel.Rows,
                )

            # Scroll to make the first selected row visible
            first_row = rows[0]
            first_idx = qt_model.index(first_row, 0)
            table.scrollTo(first_idx, QtWidgets.QAbstractItemView.PositionAtTop)

        finally:
            # Unblock signals after selection is fully restored
            selection_model.blockSignals(False)

    def eventFilter(self, obj, event):
        """Handle ESC key to deselect rows in table view."""
        if obj == self.tableView and event.type() == QtCore.QEvent.KeyPress:
            if event.key() == QtCore.Qt.Key_Escape:
                self.tableView.clearSelection()
                return True
        return super().eventFilter(obj, event)

    # =====================================
    # Layout and Sizing
    # =====================================

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

    # =====================================
    # Status & Connection Updates
    # =====================================

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
