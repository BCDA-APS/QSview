"""
Defines MainWindow class.

.. autosummary::

    ~MainWindow
"""

from logging import info
from bluesky_queueserver_api.zmq import REManagerAPI
from PyQt5 import QtCore, QtWidgets

from . import APP_TITLE, utils
from .connection_dialog import ConnectionDialog
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

    connectionChanged = QtCore.pyqtSignal(object)  # Emits the rem_api object

    def __init__(self):
        super().__init__()
        utils.myLoadUi(UI_FILE, baseinstance=self)
        self.setWindowTitle(APP_TITLE)

        # Initialize RE Manager API
        self.rem_api = None

        # Mainwindow File Menu
        self.actionOpen.triggered.connect(self.doOpen)
        self.actionOpenRecent.triggered.connect(self.doOpenRecent)
        self.actionClear.triggered.connect(self.doClear)
        self.actionAbout.triggered.connect(self.doAboutDialog)
        self.actionExit.triggered.connect(self.doClose)

        # Create widgets with connection
        self.status_widget = StatusWidget(self, rem_api=self.rem_api)
        self.groupBox_status.layout().addWidget(self.status_widget)
        self.connectionChanged.connect(self.status_widget.onConnectionChanged)

        self.plan_editor_widget = PlanEditorWidget(self, rem_api=self.rem_api)
        self.groupBox_editor.layout().addWidget(self.plan_editor_widget)
        self.connectionChanged.connect(self.plan_editor_widget.onConnectionChanged)

        self.queue_editor_widget = QueueEditorWidget(self, rem_api=self.rem_api)
        self.groupBox_queue.layout().addWidget(self.queue_editor_widget)
        self.connectionChanged.connect(self.queue_editor_widget.onConnectionChanged)

        self.history_widget = HistoryWidget(self, rem_api=self.rem_api)
        self.groupBox_history.layout().addWidget(self.history_widget)
        self.connectionChanged.connect(self.history_widget.onConnectionChanged)

        self.console_widget = ConsoleWidget(self, rem_api=self.rem_api)
        self.groupBox_console.layout().addWidget(self.console_widget)
        self.connectionChanged.connect(self.console_widget.onConnectionChanged)

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
        self.doClose()
        event.accept()  # let the window close

    def initializeConnection(self):
        """Initialize connection using the most recent server or show open dialog"""
        control_addr, info_addr = settings.getLastServerAddress()
        if control_addr and info_addr:
            self.connectToServer(control_addr, info_addr)
        else:
            self.doOpen()

    def connectToServer(self, control_addr, info_addr):
        """Connect to specified server addresses"""
        try:
            # Create new RE Manager API
            self.rem_api = REManagerAPI(
                zmq_control_addr=control_addr,
                zmq_info_addr=info_addr,
            )

            # Emit signal to widgets
            self.connectionChanged.emit(self.rem_api)

            # Save to recent servers
            settings.addRecentServer(control_addr, info_addr)
            settings.setLastServerAddress(control_addr, info_addr)

            # Update status
            self.setStatus(f"Connected to {control_addr} - {info_addr}")
            self.updateServerTitle(control_addr, info_addr)

        except Exception as e:
            self.setStatus(f"Connection failed: {e}")

    def updateServerTitle(self, control_addr, info_addr):
        """Update the status bar groupbox title with server addresses."""
        if control_addr and info_addr:
            self.groupBox_status.setTitle(f"QS Address: {control_addr} - {info_addr}")
        else:
            self.groupBox_status.setTitle("QS Address: Not Connected")
