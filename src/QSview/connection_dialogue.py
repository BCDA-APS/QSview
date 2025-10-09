"""
Connection Dialog - for configuring Queue Server connection.

.. autosummary::

    ~ConnectionDialog
"""

from PyQt5 import QtWidgets

from . import utils

UI_FILE = utils.getUiFileName(__file__)


class ConnectionDialog(QtWidgets.QDialog):
    """
    Dialog for entering Queue Server connection addresses.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        utils.myLoadUi(UI_FILE, baseinstance=self)
        self.setWindowTitle("Queue Server Address")
        self.setup()

    def setup(self):
        """Setup button box connection."""
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def getServerAddresses(self):
        """Return the entered server addresses."""
        control_addr = self.control_address.text()
        info_addr = self.info_address.text()
        return control_addr, info_addr

    def setServerAddresses(self, control_addr, info_addr):
        """Set the server addresses in the dialog."""
        self.control_address.setText(control_addr)
        self.info_address.setText(info_addr)
