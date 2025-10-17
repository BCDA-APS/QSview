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
    QueueEditorWidget,
    RunningPlanWidget,
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
        self.setup()

    def setup(self):
        """Setup model signal connections and create widgets."""
        # Connect model signals to MainWindow handlers
        self.model.connectionChanged.connect(self.onConnectionChanged)
        self.model.statusChanged.connect(self.onStatusChanged)
        self.model.messageChanged.connect(self.onMessageChanged)

        # Mainwindow File Menu
        self.actionOpen.triggered.connect(self.doOpen)
        self.actionOpenRecent.triggered.connect(self.doOpenRecent)
        self.actionClear.triggered.connect(self.doClear)
        self.actionAbout.triggered.connect(self.doAboutDialog)
        self.actionExit.triggered.connect(self.doClose)

        # Create widgets with connection
        self._setup_widget(StatusWidget, "groupBox_status", "status_widget")
        # self._setup_widget(PlanEditorWidget, "groupBox_editor", "plan_editor_widget")
        self._setup_widget(QueueEditorWidget, "groupBox_queue", "queue_editor_widget")
        self._setup_widget(HistoryWidget, "groupBox_history", "history_widget")
        self._setup_widget(ConsoleWidget, "groupBox_console", "console_widget")
        self._setup_widget(RunningPlanWidget, "groupBox_plan", "running_plan_widget")

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

    def _setup_widget(self, widget_class, parent_groupbox, widget_name):
        """
        Helper function to create a widget and connect it to model signals.

        Args:
            widget_class: The widget class to instantiate
            parent_groupbox: The groupbox to add the widget to
            widget_name: Name for the widget attribute (e.g., 'status_widget')
        """
        widget = widget_class(self, model=self.model)
        getattr(self, parent_groupbox).layout().addWidget(widget)

        # Connect model signals to widget
        self.model.connectionChanged.connect(widget.onConnectionChanged)
        self.model.statusChanged.connect(widget.onStatusChanged)

        # Store widget reference
        setattr(self, widget_name, widget)

    @property
    def message(self):
        """Returns the current message in the mainwindow status bar.

        Returns:
            str: the current message in the mainwindow status bar.
        """
        return self.statusbar.currentMessage()

    def setMessage(self, text, timeout=0):
        """Write new message to the main window status bar and terminal output."""
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
            self.setMessage("No recent servers found")
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
            self.setMessage("Recent servers cleared")

    def doClose(self, *args, **kw):
        """
        User chose exit (or quit), or closeEvent() was called.
        """
        self.setMessage("Application quitting ...")
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

    def connectToServer(self, control_addr, info_addr):
        """Connect to specified server addresses"""

        success, msg = self.model.connectToServer(control_addr, info_addr)
        if success:
            # Save to recent servers
            settings.addRecentServer(control_addr, info_addr)
            settings.setLastServerAddress(control_addr, info_addr)
        else:
            self.setMessage(f"Connection failed: {msg}")

    def onConnectionChanged(self, is_connected, control_addr, info_addr):
        """Handle connection state changes (successful connection, connection lost, disconnection)."""
        if is_connected:
            self.setMessage(f"Connected to {control_addr} - {info_addr}")
        elif control_addr == "reconnecting":
            self.setMessage("Reconnecting...")
        else:
            self.setMessage("Disconnected from the server")

    def onMessageChanged(self, msg):
        """Handle status messages from the model."""
        self.setMessage(msg)

    def onStatusChanged(self, status):
        """Handle status updates"""
        pass
