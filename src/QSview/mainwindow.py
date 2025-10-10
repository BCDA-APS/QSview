"""
Defines MainWindow class.

.. autosummary::

    ~MainWindow
"""

from PyQt5 import QtWidgets

from . import APP_TITLE, utils
from .connection_dialog import ConnectionDialog
from .queueserver_model import QueueServerModel
from .recentservers_dialog import RecentServersDialog
from .user_settings import settings
from .widgets import (
    ConsoleWidget,
    HistoryWidget,
    PlanEditorWidget,
    QueueEditorWidget,
    StatusWidget,
)

UI_FILE = utils.getUiFileName(__file__)


class MainWindow(QtWidgets.QMainWindow):
    """
    The main window of the app, built in Qt designer.

    """

    def __init__(self):
        super().__init__()
        utils.myLoadUi(UI_FILE, baseinstance=self)
        self.setWindowTitle(APP_TITLE)

        # Initialize Queue Server Model
        self.model = QueueServerModel()

        # Connect model signals to MainWindow handlers
        self.model.connectionChanged.connect(self.onConnectionChanged)
        self.model.statusChanged.connect(self.onStatusChanged)

        # Mainwindow File Menu
        self.actionOpen.triggered.connect(self.doOpen)
        self.actionOpenRecent.triggered.connect(self.doOpenRecent)
        self.actionClear.triggered.connect(self.doClear)
        self.actionAbout.triggered.connect(self.doAboutDialog)
        self.actionExit.triggered.connect(self.doClose)

        # Create widgets with connection
        self.status_widget = StatusWidget(self, model=self.model)
        self.groupBox_status.layout().addWidget(self.status_widget)
        self.model.connectionChanged.connect(self.status_widget.onConnectionChanged)
        self.model.connectionChanged.connect(self.status_widget.onStatusChanged)

        self.plan_editor_widget = PlanEditorWidget(self, model=self.model)
        self.groupBox_editor.layout().addWidget(self.plan_editor_widget)
        self.model.connectionChanged.connect(
            self.plan_editor_widget.onConnectionChanged
        )
        self.model.connectionChanged.connect(self.plan_editor_widget.onStatusChanged)

        self.queue_editor_widget = QueueEditorWidget(self, model=self.model)
        self.groupBox_queue.layout().addWidget(self.queue_editor_widget)
        self.model.connectionChanged.connect(
            self.queue_editor_widget.onConnectionChanged
        )
        self.model.connectionChanged.connect(self.queue_editor_widget.onStatusChanged)

        self.history_widget = HistoryWidget(self, model=self.model)
        self.groupBox_history.layout().addWidget(self.history_widget)
        self.model.connectionChanged.connect(self.history_widget.onConnectionChanged)
        self.model.connectionChanged.connect(self.history_widget.onStatusChanged)

        self.console_widget = ConsoleWidget(self, model=self.model)
        self.groupBox_console.layout().addWidget(self.console_widget)
        self.model.connectionChanged.connect(self.console_widget.onConnectionChanged)
        self.model.connectionChanged.connect(self.console_widget.onStatusChanged)

        # Initialize connection to Queue Server
        self.initializeConnection()

        # Splitters and stretch factors
        self.splitter_V.setSizes([90, 340, 200, 200])
        self.splitter_H1.setSizes([500, 500])
        self.splitter_H2.setSizes([500, 500])
        # Set stretch factors for each section (index, factor)
        self.splitter_V.setStretchFactor(0, 0)  # Status - fixed size (no stretch)
        self.splitter_V.setStretchFactor(1, 2)  # Middle section - gets 2x stretch
        self.splitter_V.setStretchFactor(2, 1)  # Gets 1x stretch
        self.splitter_V.setStretchFactor(3, 1)  # Gets 1x stretch

        settings.restoreWindowGeometry(self, "mainwindow_geometry")
        print("Settings are saved in:", settings.fileName())

    @property
    def status(self):
        """Returns the current message in the mainwindow status bar.

        Returns:
            str: the current message in the mainwindow status bar.
        """
        return self.statusbar.currentMessage()

    def setStatus(self, text, timeout=0):
        """Write new status to the main window and terminal output."""
        print(text)
        self.statusbar.showMessage(str(text), msecs=timeout)

    def doAboutDialog(self, *args, **kw):
        """
        Show the "About ..." dialog
        """
        from .aboutdialog import AboutDialog

        about = AboutDialog(self)
        about.open()

    def doOpen(self):
        """Open connection dialogue"""
        dialog = ConnectionDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:  # User click OK
            control_addr, info_addr = dialog.getServerAddresses()
            if control_addr and info_addr:
                self.connectToServer(control_addr, info_addr)

    def doOpenRecent(self):
        """Open recent servers dialog"""
        recent_servers = settings.getRecentServers()
        if not recent_servers:
            self.setStatus("No recent servers found")
            return
        dialog = RecentServersDialog(self, recent_servers)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:  # User click OK
            control_addr, info_addr = dialog.getServerAddresses()
            if control_addr and info_addr:
                self.connectToServer(control_addr, info_addr)

    def doClear(self):
        """Clear all recent servers from the list."""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Clear Recent Servers",
            "Are you sure you want to clear all recent servers?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        if reply == QtWidgets.QMessageBox.Yes:
            settings.clearRecentServers()
            self.setStatus("Recent servers cleared")

    def doClose(self, *args, **kw):
        """
        User chose exit (or quit), or closeEvent() was called.
        """
        self.setStatus("Application quitting ...")
        settings.saveWindowGeometry(self, "mainwindow_geometry")
        self.close()

    def closeEvent(self, event):
        """
        User clicked the big [X] to quit.
        """
        self.model.disconnectFromServer()
        self.doClose()
        event.accept()  # let the window close

    def initializeConnection(self):
        """Initialize connection using the most recent server or show open dialog"""
        control_addr, info_addr = settings.getLastServerAddress()
        if control_addr and info_addr:
            self.connectToServer(control_addr, info_addr)
        else:
            self.doOpen()

    def updateServerTitle(self, control_addr, info_addr):
        """Update the status bar groupbox title with server addresses."""
        if control_addr and info_addr:
            self.groupBox_status.setTitle(f"Connected to: {control_addr} - {info_addr}")
        else:
            self.groupBox_status.setTitle("Not Connected")

    def connectToServer(self, control_addr, info_addr):
        """Connect to specified server addresses"""

        success, msg = self.model.connectToServer(control_addr, info_addr)
        if success:
            # Save to recent servers
            settings.addRecentServer(control_addr, info_addr)
            settings.setLastServerAddress(control_addr, info_addr)
        else:
            self.setStatus(f"Connection failed: {msg}")

    def onConnectionChanged(self, is_connected, control_addr, info_addr):
        """Handle connection state changes (successful connection, connection lost, disconnection)."""
        if is_connected:
            self.setStatus(f"Connected to {control_addr} - {info_addr}")
            self.updateServerTitle(control_addr, info_addr)
        else:
            self.setStatus("Disconnected from the server")
            self.updateServerTitle("", "")

    def onStatusChanged(self, status):
        """Handle status updates"""
        pass
