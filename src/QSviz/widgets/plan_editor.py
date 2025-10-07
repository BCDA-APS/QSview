"""
Plan Editor Widget - for editing and managing plans.
"""

from PyQt5 import QtWidgets

from .. import utils


class PlanEditorWidget(QtWidgets.QWidget):
    """Plan editor widget."""

    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent=None, rm_api=None):
        super().__init__(parent)
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        """Connect signals and slots."""
        # TODO: Add signal/slot connections here
        pass
