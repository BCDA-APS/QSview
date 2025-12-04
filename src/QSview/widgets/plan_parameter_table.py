"""
Plan Parameter Table Model - for displaying and editing plan parameters.
"""

import ast
import copy
import inspect

from bluesky_queueserver import construct_parameters, format_text_descriptions
from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor


class PlanParameterTableModel(QtCore.QAbstractTableModel):
    """Table model for displaying and editing plan parameters."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Column headers
        self._column_headers = ["Parameter", "Value"]

        # Store parameters as list of dicts
        self._params = []

        # Store original item for reset functionality
        self._original_item = None

        # Store initial params state for new plans (when item_dict=None)
        self._initial_params = None

        # Store current plan name
        self._plan_name = ""

        # Store plan parameters and model for reset functionality
        self._plan_params_dict = None
        self._model = None

    def columnCount(self, parent=None):
        """Return number of columns."""
        if parent is None:
            parent = QtCore.QModelIndex()
        return len(self._column_headers)

    def rowCount(self, parent=None):
        """Return number of rows."""
        if parent is None:
            parent = QtCore.QModelIndex()
        return len(self._params)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Return header data."""
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._column_headers[section]
        return None

    def data(self, index, role=Qt.DisplayRole):
        """Return data for the given index and role."""
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        if row >= len(self._params):
            return None

        param = self._params[row]

        if role == Qt.DisplayRole:
            if col == 0:
                # Column 0: Parameter name
                param_name = param.get("name", "")
                # Add * or ** prefix for VAR_POSITIONAL or VAR_KEYWORD
                param_obj = param.get("parameter", None)
                if param_obj:
                    if param_obj.kind == inspect.Parameter.VAR_POSITIONAL:
                        return f"*{param_name}"
                    elif param_obj.kind == inspect.Parameter.VAR_KEYWORD:
                        return f"**{param_name}"
                return param_name
            elif col == 1:
                # Column 1: Parameter value
                if param.get("is_invalid", False):
                    # Show invalid string in red
                    return param.get("invalid_value_str", "")

                value = param.get("value", inspect.Parameter.empty)
                default = param.get("default", inspect.Parameter.empty)
                is_value_set = param.get("is_value_set", False)

                # Get the actual value to display
                display_value = value if is_value_set else default

                if display_value == inspect.Parameter.empty:
                    return ""

                # Format the value as string
                if isinstance(display_value, str):
                    display_str = f"'{display_value}'"
                else:
                    display_str = str(display_value)

                # Add "(default)" suffix if showing default value
                if not is_value_set:
                    display_str += " (default)"

                return display_str

        elif role == Qt.ForegroundRole:
            # Make default values grey, invalid values red
            if col == 1:
                if param.get("is_invalid", False):
                    return QColor(255, 0, 0)  # Red for invalid values

                is_value_set = param.get("is_value_set", False)
                if not is_value_set:
                    return QColor(128, 128, 128)  # Grey color for default values
            return None  # Use default color for other cases

        elif role == Qt.ToolTipRole:
            # Show parameter description as tooltip
            return param.get("description", "")

        return None

    def setData(self, index, value, role=Qt.EditRole):
        """Set data for the given index."""
        if not index.isValid():
            return False

        row = index.row()
        col = index.column()

        if row >= len(self._params):
            return False

        param = self._params[row]

        if col == 1 and role == Qt.EditRole:
            # Column 1: Edit parameter value
            value_str = str(value).strip()

            # Try to evaluate the value (parse Python literal)
            try:
                if value_str == "":
                    # Empty string means use default
                    param["value"] = param.get("default", inspect.Parameter.empty)
                    param["is_value_set"] = False
                else:
                    # Evaluate as Python literal
                    evaluated_value = ast.literal_eval(value_str)
                    param["value"] = evaluated_value
                    param["is_value_set"] = True
                    param["is_invalid"] = False
                    param.pop("invalid_value_str", None)

                # Emit signal that data changed
                self.dataChanged.emit(index, index, [role])
                return True
            except (ValueError, SyntaxError):
                # Invalid value - mark as invalid and store the invalid string
                param["is_invalid"] = True
                param["invalid_value_str"] = value_str
                # Emit signal that data changed (to update color)
                self.dataChanged.emit(index, index, [role])
                return True

        return False

    def flags(self, index):
        """Return item flags for the given index."""
        if not index.isValid():
            return Qt.NoItemFlags

        row = index.row()
        col = index.column()

        if row >= len(self._params):
            return Qt.NoItemFlags

        base_flags = Qt.ItemIsSelectable  # Base: can be selected

        if col == 0:
            # Column 0: Parameter name - enabled but not editable
            return base_flags | Qt.ItemIsEnabled

        elif col == 1:
            # Column 1: Value - enabled and editable
            return base_flags | Qt.ItemIsEnabled | Qt.ItemIsEditable

        return base_flags

    def set_plan(self, plan_name, plan_params_dict, item_dict=None, model=None):
        """Load a plan into the table model:
           takes plan data from server → converts it → stores in self._params

        Args:
            plan_name (str): Name of the plan
            plan_params_dict (dict): Plan parameters from get_allowed_plan_parameters()
            item_dict (dict, optional): Existing queue item to edit (has args/kwargs)
            model: QueueServerModel instance (needed for get_bound_item_arguments)
        """
        self.beginResetModel()  # Tell view we're about to change everything

        self._plan_name = plan_name
        self._params = []
        self._original_item = copy.deepcopy(item_dict) if item_dict else None

        # Store for reset functionality
        self._plan_params_dict = plan_params_dict
        self._model = model

        if not plan_params_dict or not model:
            self.endResetModel()
            return

        # Get parameter descriptions
        params_descriptions = format_text_descriptions(
            item_parameters=plan_params_dict, use_html=True
        )

        # Get args/kwargs from item if editing, otherwise empty
        if item_dict:
            item_args, item_kwargs = model.get_bound_item_arguments(item_dict)
            if item_args:
                # If args exist, plan can't be edited properly
                item_kwargs = dict(**{"ARGS": item_args}, **item_kwargs)
        else:
            item_args = []
            item_kwargs = {}

        # Construct inspect.Parameter objects from plan parameters
        parameters = construct_parameters(plan_params_dict.get("parameters", {}))

        # Build _params list
        for p in parameters:
            param_value = item_kwargs.get(p.name, inspect.Parameter.empty)
            is_value_set = (param_value != inspect.Parameter.empty) or (
                p.default == inspect.Parameter.empty
                and p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
            )

            is_optional = (p.default != inspect.Parameter.empty) or (
                p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
            )

            description = params_descriptions.get("parameters", {}).get(p.name, "")

            self._params.append(
                {
                    "name": p.name,
                    "value": param_value,
                    "default": p.default,
                    "is_value_set": is_value_set,
                    "is_optional": is_optional,
                    "parameter": p,
                    "description": description,
                    "is_invalid": False,
                }
            )

        # Store initial state for new plans (when item_dict is None)
        if item_dict is None:
            self._initial_params = copy.deepcopy(self._params)

        self.endResetModel()  # Tell view we're done changing

    def get_modified_item(self):
        """Convert current parameters back to item dict format.

        Returns:
            dict: Item dictionary with 'name', 'item_type', 'args', 'kwargs'
        """
        if not self._plan_name:
            return None

        # Find VAR_POSITIONAL (*args) and VAR_KEYWORD (**kwargs) parameters
        n_var_pos = -1
        n_var_kwd = -1
        for n, param in enumerate(self._params):
            if param["is_value_set"] and param["value"] != inspect.Parameter.empty:
                param_obj = param.get("parameter")
                if param_obj:
                    if param_obj.kind == inspect.Parameter.VAR_POSITIONAL:
                        n_var_pos = n
                    elif param_obj.kind == inspect.Parameter.VAR_KEYWORD:
                        n_var_kwd = n

        # Collect positional arguments (args)
        args = []
        if n_var_pos >= 0:
            # Has *args parameter
            var_pos_value = self._params[n_var_pos]["value"]
            if not isinstance(var_pos_value, (list, tuple)):
                raise ValueError(f"Invalid type for VAR_POSITIONAL: {var_pos_value}")

            # Add all positional args before *args
            for n in range(n_var_pos):
                param = self._params[n]
                if param["is_value_set"] and param["value"] != inspect.Parameter.empty:
                    args.append(param["value"])

            # Add *args values
            args.extend(var_pos_value)
        else:
            # No *args, collect regular positional args
            for param in self._params:
                param_obj = param.get("parameter")
                if param_obj and param_obj.kind == inspect.Parameter.POSITIONAL_ONLY:
                    if (
                        param["is_value_set"]
                        and param["value"] != inspect.Parameter.empty
                    ):
                        args.append(param["value"])

        # Collect keyword arguments (kwargs)
        kwargs = {}

        # Determine range for regular kwargs
        n_start = 0 if n_var_pos < 0 else n_var_pos + 1
        n_stop = len(self._params) if n_var_kwd < 0 else n_var_kwd

        # Collect regular kwargs
        for n in range(n_start, n_stop):
            param = self._params[n]
            if param["is_value_set"] and param["value"] != inspect.Parameter.empty:
                param_obj = param.get("parameter")
                if param_obj and param_obj.kind not in (
                    inspect.Parameter.VAR_POSITIONAL,
                    inspect.Parameter.VAR_KEYWORD,
                    inspect.Parameter.POSITIONAL_ONLY,
                ):
                    kwargs[param["name"]] = param["value"]

        # Add **kwargs if present
        if n_var_kwd >= 0:
            var_kwd_value = self._params[n_var_kwd]["value"]
            if not isinstance(var_kwd_value, dict):
                raise ValueError(f"Invalid type for VAR_KEYWORD: {var_kwd_value}")
            kwargs.update(var_kwd_value)

        # Build item dict
        item = {
            "name": self._plan_name,
            "item_type": "plan",
            "args": args,
            "kwargs": kwargs,
        }

        # If editing existing item, preserve item_uid
        if self._original_item and "item_uid" in self._original_item:
            item["item_uid"] = self._original_item["item_uid"]

        return item

    def reset_item(self):
        """Reset parameters to original values.

        - If editing existing plan: resets to _original_item values
        - If creating new plan: resets to initial state (required empty, optional with defaults)
        """
        if not self._plan_params_dict or not self._model:
            # Missing plan data
            return

        if self._original_item:
            # Editing existing plan - reset to original item values
            self.set_plan(
                plan_name=self._plan_name,
                plan_params_dict=self._plan_params_dict,
                item_dict=self._original_item,
                model=self._model,
            )
        elif self._initial_params:
            # Creating new plan - reset to initial state
            self.beginResetModel()
            self._params = copy.deepcopy(self._initial_params)
            self.endResetModel()
