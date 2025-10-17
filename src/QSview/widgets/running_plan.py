"""
Running Plan Widget - for editing and managing the queue.
"""

from PyQt5 import QtWidgets

from .. import utils


class RunningPlanWidget(QtWidgets.QWidget):
    """Queue editor widget."""

    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent=None, model=None):
        super().__init__(parent)
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()
        self.model = model

    def setup(self):
        """Connect signals and slots."""
        # TODO: Add signal/slot connections here
        pass

    def onConnectionChanged(self, is_connected, control_addr, info_addr):
        """Handle connection changes from QueueServerModel signal."""
        # TODO: Add connection-dependent updates here
        pass

    def onStatusChanged(self, is_connected, status):
        """Handle periodic status updates from model (every 1s)."""
        if not is_connected:
            # Clear display when disconnected
            self.planTextEdit.setPlainText("")
            return

        # Get running item UID from status
        running_item_uid = status.get("running_item_uid", None)

        if not running_item_uid:
            # No plan running - clear display
            self.planTextEdit.setPlainText("")
            return

        # Get full running item details from model
        running_item = self.model.getRunningItem()
        run_list = self.model.getRunList()

        # Format and display the information
        display_text = self._formatRunningPlanInfo(running_item, run_list)
        self.planTextEdit.setPlainText(display_text)

    def _formatRunningPlanInfo(self, running_item, run_list):
        """
        Format the running plan and run list information for display.

        Args:
            running_item (dict): Running item information from model
            run_list (list): List of runs from model

        Returns:
            str: Formatted text for display
        """
        if not running_item:
            return "No plan details available."

        # Extract plan information
        plan_name = running_item.get("name", "Unknown")
        args = running_item.get("args", [])
        kwargs = running_item.get("kwargs", {})

        # Build the display text
        text_lines = []

        # Plan Name section
        text_lines.append(f"Plan Name: {plan_name}")
        text_lines.append("")

        # Parameters section
        text_lines.append("Parameters:")

        # Add args if present
        if args:
            args_str = str(args)[1:-1]  # Remove brackets
            text_lines.append(f"  args: {args_str}")

        # Add kwargs
        if kwargs:
            for key, value in kwargs.items():
                text_lines.append(f"  {key}: {value}")

        # If no parameters at all
        if not args and not kwargs:
            text_lines.append("  (No parameters)")

        text_lines.append("")

        # Runs section
        text_lines.append("Runs:")

        if run_list:
            for run_info in run_list:
                run_uid = run_info.get("uid", "Unknown")
                is_open = run_info.get("is_open", False)
                exit_status = run_info.get("exit_status", "")
                scan_id = run_info.get("scan_id", "Unknown")
                text_lines.append(f"  uid: {run_uid}")
                text_lines.append(f"  scan_id: {scan_id}")
                if is_open:
                    text_lines.append("  Exit status: In progress...")
                else:
                    text_lines.append(f"  Exit status: {exit_status}")
        else:
            text_lines.append("  (No runs recorded yet)")

        return "\n".join(text_lines)
