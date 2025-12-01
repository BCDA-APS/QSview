"""
Plan Editor Dialog - for creating new plans and editing existing ones.
"""

import inspect
from PyQt5 import QtWidgets, QtCore

from .. import utils
from .plan_parameter_table import PlanParameterTableModel


class PlanEditorDialog(QtWidgets.QDialog):
    """Plan editor dialog for creating and editing plans."""

    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent=None, model=None):
        super().__init__(parent)
        utils.myLoadUi(self.ui_file, baseinstance=self)

        self.model = model  # QueueServerModel instance
        self.table_model = PlanParameterTableModel(parent=self)
        self._editing_item = None  # Track if editing existing item

        self.setup()

    def setup(self):
        """Set up UI components and connect signals."""
        # Set up table view
        self.tableView.setModel(self.table_model)

        # Set column widths
        self.tableView.setColumnWidth(0, 200)  # Parameter name
        self.tableView.setColumnWidth(1, 30)  # Checkbox
        self.tableView.setColumnWidth(2, 300)  # Value

        # Connect button signals
        self.addPlanButton.clicked.connect(self.on_add_plan)
        self.resetButton.clicked.connect(self.on_reset)
        self.cancelButton.clicked.connect(self.reject)
        self.planSelectBox.currentTextChanged.connect(self.on_plan_selected)

        # Connect table model dataChanged signal to update button states
        self.table_model.dataChanged.connect(self.update_button_states)

        # Initial button states
        self.update_button_states()
        self.saveButton.setVisible(False)

        # Populate plan selection if model is available
        if self.model:
            self.populate_plan_selection()

    def populate_plan_selection(self):
        """Populate the plan selection combobox with allowed plans."""
        if not self.model or not self.model._is_connected:
            return

        # Get allowed plan names
        plan_names = self.model.get_allowed_plan_names()

        # Clear existing items
        self.planSelectBox.clear()

        # Add plans to combobox
        for plan_name in plan_names:
            self.planSelectBox.addItem(plan_name)

    def on_plan_selected(self, plan_name):
        """Handle plan selection from combobox."""
        if not plan_name or not self.model:
            return

        # Get plan parameters
        plan_params = self.model.get_allowed_plan_parameters(name=plan_name)

        if not plan_params:
            return

        # Load plan into table model
        self.table_model.set_plan(
            plan_name=plan_name,
            plan_params_dict=plan_params,
            item_dict=None,  # Creating a new plan, not editing
            model=self.model,
        )

        # Update button states
        self._editing_item = None
        self.update_button_states()

    def on_add_plan(self):
        """Handle Add Plan button click - adds new plan to queue."""
        if not self.model:
            return

        # Get the modified item from table model
        item = self.table_model.get_modified_item()
        if not item:
            self.model.messageChanged.emit("No plan selected")
            return

        try:
            if self._editing_item:
                # Editing existing plan - update it
                self.model.queue_item_update(item)
                self.model.messageChanged.emit(f"Plan '{item['name']}' updated")
            else:
                # Creating new plan - add it
                self.model.queue_item_add(item)
                self.model.messageChanged.emit(f"Plan '{item['name']}' added to queue")
            # Delay closing to show success message
            QtCore.QTimer.singleShot(500, self.accept)
        except Exception as e:
            self.model.messageChanged.emit(f"Error adding plan: {e}")

    def on_reset(self):
        """Handle Reset button click - resets parameters to original values."""
        self.table_model.reset_item()

    def update_button_states(self):
        """Update button enable/disable states based on current mode."""
        has_plan = bool(self.table_model._plan_name)

        # Check if all required parameters have values
        all_required_set = True
        if has_plan:
            for param in self.table_model._params:
                if not param.get("is_optional", False):  # Required parameter
                    if not param.get("is_value_set", False):
                        all_required_set = False
                        break
                    if param.get("value") == inspect.Parameter.empty:
                        all_required_set = False
                        break

        is_valid = has_plan and all_required_set

        self.addPlanButton.setEnabled(is_valid)

    def open_for_editing(self, item_dict):
        """Open dialog for editing an existing queue item.

        Args:
            item_dict (dict): Queue item dictionary to edit
        """
        if not item_dict or not self.model:
            return

        # Store the item being edited
        self._editing_item = item_dict

        # Get plan name from item
        plan_name = item_dict.get("name")
        if not plan_name:
            return

        # Get plan parameters
        plan_params = self.model.get_allowed_plan_parameters(name=plan_name)
        if not plan_params:
            self.model.messageChanged.emit(
                f"Plan '{plan_name}' not found in allowed plans"
            )
            return

        # Load plan into table model with existing item data
        self.table_model.set_plan(
            plan_name=plan_name,
            plan_params_dict=plan_params,
            item_dict=item_dict,
            model=self.model,
        )

        # Set plan in combobox (if it exists)
        index = self.planSelectBox.findText(plan_name)
        if index >= 0:
            self.planSelectBox.setCurrentIndex(index)

        # Update button states (editing mode)
        self.update_button_states()

        # Optionally update window title
        self.setWindowTitle(f"Edit Plan: {plan_name}")
