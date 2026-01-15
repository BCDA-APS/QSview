"""
Defines MainWindow class.

.. autosummary::

    ~MainWindow
"""

import csv
import logging

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

logger = logging.getLogger(__name__)

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
        self.actionSaveHistory.triggered.connect(self.doSaveHistory)

        # History sorting order
        self.actionSortNewestFirst.triggered.connect(self.doHistorySortToggle)
        self.actionSortNewestFirst.setChecked(settings.getHistorySortNewestFirst())

        # Create widgets with connection
        self._setup_widget(StatusWidget, "groupBox_status", "status_widget")
        self._setup_widget(QueueEditorWidget, "groupBox_queue", "queue_editor_widget")
        self._setup_widget(HistoryWidget, "groupBox_history", "history_widget")
        self._setup_widget(ConsoleWidget, "groupBox_console", "console_widget")
        self._setup_widget(RunningPlanWidget, "groupBox_plan", "running_plan_widget")

        # Initialize connection to Queue Server
        self.initializeConnection()

        # Splitters and stretch factors
        self.splitter_V.setSizes([90, 340, 200, 200])
        self.splitter_H2.setSizes([300, 700])
        # Set stretch factors for each section (index, factor)
        self.splitter_V.setStretchFactor(0, 0)  # Status - fixed size (no stretch)
        self.splitter_V.setStretchFactor(1, 2)  # Middle section - gets 2x stretch
        self.splitter_V.setStretchFactor(2, 1)  # Gets 1x stretch
        self.splitter_V.setStretchFactor(3, 1)  # Gets 1x stretch

        settings.restoreWindowGeometry(self, "mainwindow_geometry")
        logger.info(f"Settings are saved in: {settings.fileName()}")

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

    # ========================================
    # Status Bar Messages
    # ========================================

    @property
    def message(self):
        """Returns the current message in the mainwindow status bar.

        Returns:
            str: the current message in the mainwindow status bar.
        """
        return self.statusbar.currentMessage()

    def setMessage(self, text, timeout=0):
        """Write new message to the main window status bar and terminal output."""
        logger.debug("%s", text)
        self.statusbar.showMessage(str(text), msecs=timeout)

    # ========================================
    # Menu Control
    # ========================================

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

    def doHistorySortToggle(self):
        """Toggle history sort direction."""

        # Toggle the settings
        current = settings.getHistorySortNewestFirst()
        settings.setHistorySortNewestFirst(not current)
        self.actionSortNewestFirst.setChecked(not current)

        # Refresh the history display widget if it exist
        if hasattr(self, "history_widget"):
            history_data = self.model.getHistory() if self.model else []
            self.history_widget._on_history_changed(history_data)

    # ========================================
    # Save History
    # ========================================

    def doSaveHistory(self):
        """Save history to file"""
        history_data = self.model.getHistory()
        history_data = self.history_widget._apply_sort_setting(history_data)
        if not history_data:
            self.setMessage("No history to save")
            return
        rows = []
        for history_item in history_data:
            row_data = self.extract_row_data(history_item)
            rows.append(row_data)
        sorting = "newest" if settings.getHistorySortNewestFirst() else "oldest"
        self.writeHistoryFile(rows, sorting)

    def writeHistoryFile(self, rows, sorting):
        """Write CSV file"""
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save History",
            "",  # start directory (empty = default)
            "CSV Files (*.csv);;All Files (*)",
        )
        if not filename:
            return
        try:
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    ["Status", "Name", "Detector", "Arguments", "Metadata", "User"]
                )
                for row in rows:
                    writer.writerow(row)
                writer.writerow([])
                writer.writerow([f"Sorted {sorting} first."])
                self.setMessage(f"History saved to {filename}")
        except Exception as e:
            self.setMessage(f"Error saving history: {e}")

    def extract_row_data(self, history_item):
        """Extract data for a single row from history item."""
        result = history_item.get("result", {})

        # Get bound arguments (converts positional args to kwargs with proper names)
        if self.model:
            args, kwargs = self.model.get_bound_item_arguments(history_item)
        else:
            args = history_item.get("args", [])
            kwargs = history_item.get("kwargs", {}).copy()

        # Combine args and kwargs for formatting
        if args:
            kwargs["args"] = args

        arguments = self.extract_arguments(kwargs)

        return [
            result.get("exit_status", "Unknown"),  # Status
            history_item.get("name", "Unknown"),  # Name
            arguments.get("det", ""),  # Detector
            arguments.get("args", ""),  # Arguments
            arguments.get("md", ""),  # Metadata
            history_item.get("user", "Unknown"),  # User
        ]

    def extract_arguments(self, kwargs):
        """Extract det, args and md from kwargs; returns a dictionary"""
        columns = {}
        if not kwargs:
            return {}
        if "detectors" in kwargs:
            columns["det"] = kwargs["detectors"]
        other_kwargs = {k: v for k, v in kwargs.items() if k not in ["detectors", "md"]}
        if other_kwargs:
            columns["args"] = other_kwargs
        if "md" in kwargs:
            columns["md"] = kwargs["md"]
        return columns

    # ========================================
    # Connection Control
    # ========================================

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
