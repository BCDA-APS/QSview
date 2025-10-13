"""
Recent Servers Dialog - for selecting from recently used Queue Server connections.

.. autosummary::

    ~RecentServersDialogue
"""

from PyQt5 import QtWidgets

from . import utils

UI_FILE = utils.getUiFileName(__file__)


class RecentServersDialog(QtWidgets.QDialog):
    """
    Dialog for selecting recent servers.
    """

    def __init__(self, parent=None, recent_servers=None):
        super().__init__(parent)
        utils.myLoadUi(UI_FILE, baseinstance=self)
        self.setWindowTitle("Recent Servers")
        self.selected_server_entry = None
        self.setup(recent_servers or [])

    def setup(self, recent_servers):
        """Setup dialog with recent servers."""
        # Populate recent servers dropdown
        self.recent_servers.clear()
        self.recent_servers.addItem("Select a recent server...")

        for server_entry in recent_servers:
            if ";" in server_entry:
                # First item is display text, second is data
                self.recent_servers.addItem(server_entry, server_entry)

        # Connect signals
        self.recent_servers.activated.connect(self.onRecentServerSelected)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def onRecentServerSelected(self, index):
        """Handle selection of recent server."""
        if index > 0:  # Skip the first item (placeholder)
            self.selected_server_entry = self.recent_servers.itemData(index)
        else:
            self.selected_server_entry = None

    def getServerAddresses(self):
        """Return the entered server addresses."""
        if self.selected_server_entry and ";" in self.selected_server_entry:
            control_addr, info_addr = self.selected_server_entry.split(";")
        else:
            control_addr = None
            info_addr = None
        return control_addr, info_addr
