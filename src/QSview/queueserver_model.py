"""
Queue Server Model - manages connection state and data for the Queue Server.

This model follows the MVC pattern, handling all Queue Server API interactions
and emitting signals when state changes occur.

.. autosummary::

    ~QueueServerModel
"""

from bluesky_queueserver_api.zmq import REManagerAPI
from PyQt5 import QtCore


class QueueServerModel(QtCore.QObject):
    """
    Model for Queue Server connection and state management.

    This class manages the connection to the Queue Server, maintains application
    state, and emits signals when state changes occur. Widgets connect to
    these signals to update their displays.

    Signals:
        connectionChanged(bool, str, str): Emitted when connection state changes.
            Args: (is_connected, control_addr, info_addr)
        statusChanged(dict): Emitted when server status is updated.
            Args: (status_dict)
        queueChanged(dict): Emitted when queue items change.
            Args: (queue_dict)
        historyChanged(dict): Emitted when history changes.
            Args: (history_dict)
    """

    # Signals
    connectionChanged = QtCore.pyqtSignal(bool, str, str)
    statusChanged = QtCore.pyqtSignal(object)
    queueChanged = QtCore.pyqtSignal(object)
    historyChanged = QtCore.pyqtSignal(object)

    def __init__(self):
        super().__init__()

        # Connection state
        self._rem_api = None
        self._is_connected = False
        self._control_addr = ""
        self._info_addr = ""

        # Reconnection state
        self._last_successful_control_addr = ""
        self._last_successful_info_addr = ""
        self._is_reconnecting = False

        # Cached state
        self._status = {}
        self._queue = {}
        self._history = {}

        # Timer for periodic status updates
        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self._update_status)
        self._update_interval = 2000  # 2s

    def connectToServer(self, control_addr, info_addr):
        """
        Connect to the Queue Server.

        Args:
            control_addr (str): Control address (e.g., "tcp://localhost:60615")
            info_addr (str): Info address (e.g., "tcp://localhost:60625")

        Returns:
            tuple: (success: bool, error_message: str or None)
        """

        try:
            # Create API connection
            self._rem_api = REManagerAPI(
                zmq_control_addr=control_addr, zmq_info_addr=info_addr
            )

            # Test connection by getting status
            status = self._rem_api.status()

            # Connection successful
            self._is_connected = True
            self._control_addr = control_addr
            self._info_addr = info_addr
            self._status = status

            # Save for reconnection
            self._last_successful_control_addr = control_addr
            self._last_successful_info_addr = info_addr

            # Start periodic updates
            self._timer.start(self._update_interval)

            # Emit connection state changed
            self.connectionChanged.emit(True, control_addr, info_addr)

            # Emit initial status
            self.statusChanged.emit(self._status)

            return (True, None)

        except Exception as e:
            # Connection failed
            self._is_connected = False
            self._rem_api = None
            self._control_addr = ""
            self._info_addr = ""
            # Emit disconnection connection state changed
            self.connectionChanged.emit(False, "", "")
            return (False, str(e))

    def disconnectFromServer(self):
        """
        Disconnect from the Queue Server.

        This is called internally when:
        - Connection is lost (detected in _update_status)
        - User connects to a different server
        - Application is shutting down
        """
        # Stop periodic updates
        self._timer.stop()

        # Clear connection
        self._rem_api = None
        self._is_connected = False
        self._is_reconnecting = False

        # Clear cached state
        self._status = {}
        self._queue = {}
        self._history = {}

        # Emit disconnection
        self.connectionChanged.emit(False, self._control_addr, self._info_addr)

    def attemptReconnect(self):
        """Attempt to reconnect to the last successful server."""
        if self._is_reconnecting:
            return  # Already trying to reconnect

        if (
            not self._last_successful_control_addr
            or not self._last_successful_info_addr
        ):
            print("No previous connection to reconnect to")
            return

        self._is_reconnecting = True
        print(f"Attempting to reconnect to {self._last_successful_control_addr}")

        # Emit reconnecting signal
        self.connectionChanged.emit(False, "reconnecting", "")
        success, msg = self.connectToServer(
            self._last_successful_control_addr, self._last_successful_info_addr
        )
        self._is_reconnecting = False
        if not success:
            print(f"Reconnection failed: {msg}")

    def _update_status(self):
        """
        Periodic status update (called by timer).

        This method is called every 2 seconds to update the server status.
        If the connection fails, it will automatically disconnect.
        """
        if not self._rem_api or not self._is_connected:
            return

        try:
            # Get current status
            self._status = self._rem_api.status()

            # Emit signal - TODO: should we check for changes to emit or always emit?
            self.statusChanged.emit(self._status)

        except Exception as e:
            # Connection lost
            print(f"Connection lost: {e}")
            self.disconnectFromServer()

    def isConnected(self):
        """
        Check if currently connected to a server.

        Returns:
            bool: True if connected, False otherwise
        """
        return self._is_connected

    def getConnectionInfo(self):
        """
        Get current connection information.

        Returns:
            tuple: (control_addr, info_addr)
        """
        return (self._control_addr, self._info_addr)

    def getREManagerAPI(self):
        """
        Get the underlying REManagerAPI object.

        Returns:
            REManagerAPI or None: The API object if connected, None otherwise
        """
        return self._rem_api if self._is_connected else None

    def getStatus(self):
        """
        Get the cached server status.

        Returns:
            dict: The most recent status dictionary
        """
        return self._status.copy()

    def refreshStatus(self):
        """Force an immediate status update (outside of timer)."""
        self._update_status()
