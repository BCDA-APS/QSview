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
        self.model = model

    def onConnectionChanged(self, is_connected, control_addr, info_addr):
        """Handle connection changes from QueueServerModel signal."""
        # TODO: Add connection-dependent updates here
        pass

    def onStatusChanged(self, is_connected, status):
        """Handle periodic status updates from model (every 1s)."""
        if not is_connected:
            # Clear display when disconnected
            self.planTextEdit.setHtml(
                "<p style='color: gray; font-style: italic;'>Disconnected from Queue Server.</p>"
            )
            return

        # Get running item UID from status
        running_item_uid = status.get("running_item_uid", None)

        if not running_item_uid:
            # No plan running - clear display
            self.planTextEdit.setHtml(
                "<p style='color: gray; font-style: italic;'>No plan currently running.</p>"
            )
            return

        # Save current scroll position BEFORE updating content
        scrollbar = self.planTextEdit.verticalScrollBar()
        old_scroll_position = scrollbar.value()

        # Get full running item details from model
        running_item = self.model.getRunningItem()
        run_list = self.model.getRunList()

        # Format and display the information
        display_text = self._formatRunningPlanInfo(running_item, run_list)
        self.planTextEdit.setHtml(display_text)

        # Restore scroll position AFTER updating content
        scrollbar.setValue(old_scroll_position)

    def _formatRunningPlanInfo(self, running_item, run_list):
        """
        Format the running plan and run list information for display with HTML styling.

        Args:
            running_item (dict): Running item information from model
            run_list (list): List of runs from model

        Returns:
            str: Formatted HTML text for display
        """
        if not running_item:
            return "<p style='color: gray; font-style: italic;'>No plan details available.</p>"

        # Extract plan information
        plan_name = running_item.get("name", "Unknown")
        args = running_item.get("args", [])
        kwargs = running_item.get("kwargs", {})

        # Build the display text with HTML styling
        text_lines = []

        # Plan Name section with styling
        text_lines.append(
            f"<b>Plan Name:</b> <span style='color: #4a5568;'>{plan_name}</span><br>"
        )

        # Parameters section
        text_lines.append("<b>Parameters:</b><br>")

        # Add args if present
        if args:
            args_str = str(args)[1:-1]  # Remove brackets
            text_lines.append(
                f"<b style='color: #2d3748;'>&nbsp;&nbsp;&nbsp;args: </b> <span style='color: #4a5568;'>{args_str}</span><br>"
            )

        # Add kwargs
        if kwargs:
            for key, value in kwargs.items():
                text_lines.append(
                    f"<b style='color: #2d3748;'>&nbsp;&nbsp;&nbsp;{key}:</b> <span style='color: #4a5568;'> {value}</span><br>"
                )

        # If no parameters at all
        if not args and not kwargs:
            text_lines.append("&nbsp;&nbsp;&nbsp;(No parameters)<br>")

        text_lines.append("<br>")

        # Runs section
        text_lines.append("<b>Runs:</b><br>")

        if run_list:
            for run_info in run_list:
                run_uid = run_info.get("uid", "Unknown")
                is_open = run_info.get("is_open", False)
                exit_status = run_info.get("exit_status", "")
                scan_id = run_info.get("scan_id", "Unknown")

                # Color coding for status
                if is_open:
                    status_color = "#3182ce"  # Blue for in progress
                    status_text = "In progress..."
                elif exit_status == "success":
                    status_color = "#38a169"  # Green for success
                    status_text = exit_status
                elif exit_status == "failed":
                    status_color = "#e53e3e"  # Red for failed
                    status_text = exit_status
                else:
                    status_color = "#805ad5"  # Purple for other statuses
                    status_text = exit_status

                # text_lines.append(
                #     f"<div style='margin-left: 20px; margin-bottom: 5px;'>"
                # )
                text_lines.append(
                    f"<b style='color: #2d3748;'>&nbsp;&nbsp;&nbsp;uid:</b> <span style='color: #4a5568; font-family: monospace;'>{run_uid}</span><br>"
                )
                text_lines.append(
                    f"<b style='color: #2d3748;'>&nbsp;&nbsp;&nbsp;scan_id:</b> <span style='color: #4a5568;'>{scan_id}</span><br>"
                )
                text_lines.append(
                    f"<b style='color: #2d3748;'>&nbsp;&nbsp;&nbsp;Exit status:</b> <span style='color: {status_color}; font-weight: bold;'>{status_text}</span><br>"
                )
                text_lines.append("</div>")
        else:
            text_lines.append(
                "<span style='margin-left: 20px; color: gray; font-style: italic;'>(No runs recorded yet)</span><br>"
            )

        return "".join(text_lines)
