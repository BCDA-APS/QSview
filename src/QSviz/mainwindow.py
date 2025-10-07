"""
Defines MainWindow class.

.. autosummary::

    ~MainWindow
"""

from PyQt5 import QtWidgets

from . import APP_TITLE, utils
from .user_settings import settings
from bluesky_queueserver_api.zmq import REManagerAPI

from .widgets import (
    StatusWidget,
    PlanEditorWidget,
    QueueEditorWidget,
    HistoryWidget,
    ConsoleWidget,
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

        # self.actionOpen.triggered.connect(self.doOpen)
        self.actionAbout.triggered.connect(self.doAboutDialog)
        self.actionExit.triggered.connect(self.doClose)

        # Create QServer connection
        self.rem_api = REManagerAPI(
            zmq_control_addr="tcp://wow.xray.aps.anl.gov:60615",
            zmq_info_addr="tcp://wow.xray.aps.anl.gov:60625",
        )

        # Create widgets with connection
        self.status_widget = StatusWidget(self, rem_api=self.rem_api)
        self.groupBox_status.layout().addWidget(self.status_widget)

        self.plan_editor_widget = PlanEditorWidget(self, rem_api=self.rem_api)
        self.groupBox_editor.layout().addWidget(self.plan_editor_widget)

        self.queue_editor_widget = QueueEditorWidget(self, rem_api=self.rem_api)
        self.groupBox_queue.layout().addWidget(self.queue_editor_widget)

        self.history_widget = HistoryWidget(self, rem_api=self.rem_api)
        self.groupBox_history.layout().addWidget(self.history_widget)

        self.console_widget = ConsoleWidget(self, rem_api=self.rem_api)
        self.groupBox_console.layout().addWidget(self.console_widget)

        # Splitters and stretch factors
        self.splitter_V.setSizes([120, 340, 200])
        self.splitter_H1.setSizes([500, 500])
        self.splitter_H2.setSizes([500, 500])
        self.splitter_V.setStretchFactor(1, 2)

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

    def closeEvent(self, event):
        """
        User clicked the big [X] to quit.
        """
        self.doClose()
        event.accept()  # let the window close

    def doClose(self, *args, **kw):
        """
        User chose exit (or quit), or closeEvent() was called.
        """
        self.setStatus("Application quitting ...")
        settings.saveWindowGeometry(self, "mainwindow_geometry")
        self.close()
