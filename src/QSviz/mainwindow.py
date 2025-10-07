"""
Defines MainWindow class.

.. autosummary::

    ~MainWindow
"""

from PyQt5 import QtWidgets

from . import APP_TITLE, utils
from .user_settings import settings

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

        # Status bar
        status_widget = QtWidgets.QWidget()
        utils.myLoadUi("statusbar.ui", baseinstance=status_widget)
        self.groupBox_status.layout().addWidget(status_widget)

        # Queue editor
        queue_widget = QtWidgets.QWidget()
        utils.myLoadUi("queueeditor.ui", baseinstance=queue_widget)
        self.groupBox_queue.layout().addWidget(queue_widget)

        # History editor
        history_widget = QtWidgets.QWidget()
        utils.myLoadUi("historyeditor.ui", baseinstance=history_widget)
        self.groupBox_history.layout().addWidget(history_widget)

        # Console
        console_widget = QtWidgets.QWidget()
        utils.myLoadUi("console.ui", baseinstance=console_widget)
        self.groupBox_console.layout().addWidget(console_widget)

        self.splitter_V.setSizes([120, 340, 200])
        self.splitter_H.setSizes([500, 500])
        # optional ratios
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

    # def doOpen(self, *args, **kw):
    #     """
    #     User chose to open (connect with) a queue server.
    #     """
    #     from .opendialog import OpenDialog

    #     self.setStatus("Please select a server...")
    #     open_dialog = OpenDialog(self)

    # def doPopUp(self, message):
    #     """
    #     User chose to open (connect with) a tiled server.
    #     """
    #     from .popup import PopUp

    #     popup = PopUp(self, message)
    #     return popup.exec_() == QtWidgets.QDialog.Accepted

    # def proceed(self):
    #     """Handle the logic when the user clicks 'OK'."""
    #     return True

    # def cancel(self):
    #     """Handle the logic when the user clicks 'Cancel'."""
    #     return False
