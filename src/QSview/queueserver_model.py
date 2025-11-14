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
        statusChanged(is_connected, dict): Emitted when server status is updated.
            Args: (status_dict)
        queueChanged(dict): Emitted when queue items change.
            Args: (queue_dict)
        historyChanged(dict): Emitted when history changes.
            Args: (history_dict)
    """

    # Signals
    connectionChanged = QtCore.pyqtSignal(bool, str, str)
    statusChanged = QtCore.pyqtSignal(bool, object)
    messageChanged = QtCore.pyqtSignal(str)
    queueChanged = QtCore.pyqtSignal(object)
    queueNeedsUpdate = QtCore.pyqtSignal()
    queueSelectionChanged = QtCore.pyqtSignal(list)
    historyChanged = QtCore.pyqtSignal(object)
    historyNeedsUpdate = QtCore.pyqtSignal()

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
        self._history_uid = ""
        self._queue_uid = ""
        self._selected_queue_item_uids = []

        # User info
        self._user_name = "GUI Client"
        self._user_group = "primary"

        # Timer for periodic status updates
        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self.fetchStatus)
        self._update_interval = 500  # 0.5s

        # Console monitoring
        self._stop_console_monitor = False

    # ========================================
    # RE Manager Methods
    # ========================================

    def getREManagerAPI(self):
        """
        Get the underlying REManagerAPI object.

        Returns:
            REManagerAPI or None: The API object if connected, None otherwise
        """
        return self._rem_api if self._is_connected else None

    # ========================================
    # Connection Methods
    # ========================================

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
            self._queue_uid = status.get("plan_queue_uid", "")
            self._history_uid = status.get("plan_history_uid", "")

            # Save for reconnection
            self._last_successful_control_addr = control_addr
            self._last_successful_info_addr = info_addr

            # Start periodic updates
            self._timer.start(self._update_interval)

            # Emit connection state changed
            self.connectionChanged.emit(True, control_addr, info_addr)

            # Emit initial status
            self.statusChanged.emit(True, self._status)

            return (True, None)

        except Exception as e:
            # Connection failed
            self._is_connected = False
            self._rem_api = None
            self._control_addr = ""
            self._info_addr = ""
            # Emit disconnection connection state changed
            self.connectionChanged.emit(False, "", "")
            self.statusChanged.emit(False, {})
            return (False, str(e))

    def disconnectFromServer(self):
        """
        Disconnect from the Queue Server.

        This is called internally when:
        - Connection is lost (detected in fetchStatus)
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
        self.statusChanged.emit(False, {})

    def attemptReconnect(self):
        """Attempt to reconnect to the last successful server."""
        if self._is_reconnecting:
            return  # Already trying to reconnect

        if (
            not self._last_successful_control_addr
            or not self._last_successful_info_addr
        ):
            self.messageChanged.emit("No previous connection to reconnect to")
            return

        self._is_reconnecting = True
        self.messageChanged.emit(
            f"Attempting to reconnect to {self._last_successful_control_addr}"
        )

        # Emit reconnecting signal
        self.connectionChanged.emit(False, "reconnecting", "")
        success, msg = self.connectToServer(
            self._last_successful_control_addr, self._last_successful_info_addr
        )
        self._is_reconnecting = False
        if not success:
            self.messageChanged.emit(f"Reconnection failed: {msg}")

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

    # ========================================
    # Update Status
    # ========================================

    def fetchStatus(self):
        """
        Periodic status update (called by timer).

        This method is called every 0.5 seconds to update the server status.
        If the connection fails, it will automatically disconnect.
        """
        if not self._rem_api or not self._is_connected:
            return

        try:
            # Get current status
            self._status = self._rem_api.status()

            # Check if history UID has changed
            new_history_uid = self._status.get("plan_history_uid", "")
            if new_history_uid != self._history_uid:
                self._history_uid = new_history_uid
                self.historyNeedsUpdate.emit()

            # Check if queue UID has changed
            new_queue_uid = self._status.get("plan_queue_uid", "")
            if new_queue_uid != self._queue_uid:
                self._queue_uid = new_queue_uid
                self.queueNeedsUpdate.emit()

            # Emit signal
            self.statusChanged.emit(self._is_connected, self._status)

        except Exception as e:
            # Connection lost
            self.messageChanged.emit(f"Connection lost: {e}")
            self.disconnectFromServer()

    def getStatus(self):
        """
        Get the cached server status.

        Returns:
            dict: The most recent status dictionary
        """
        return self._status.copy()

    # ========================================
    # Queue Methods
    # ========================================

    @property
    def selected_queue_item_uids(self):
        """Return the cached list of selected queue item UIDs."""

        return list(self._selected_queue_item_uids)

    @selected_queue_item_uids.setter
    def selected_queue_item_uids(self, uids):
        """Store the current queue selection as a list of UIDs."""

        uids = list(uids)
        if uids != self._selected_queue_item_uids:
            self._selected_queue_item_uids = uids

    def add_items_to_queue(self, items):
        """Add multiple items to the queue."""
        if not self._rem_api or not self._is_connected:
            self.messageChanged.emit("Not connected to server")
            return

        try:
            # Add user info to each item
            request_params = {
                "items": items,
                "user": self._user_name,
                "user_group": self._user_group,
            }

            # Add items to the back of the queue
            response = self._rem_api.item_add_batch(**request_params)
            if response.get("success", False):
                try:
                    original_uids = [
                        item.get("item_uid") for item in items if item.get("item_uid")
                    ]
                    if original_uids:
                        self.selected_queue_item_uids = original_uids
                except Exception as e:
                    # If extraction fails, clear selection (items added but can't select them)
                    self.messageChanged.emit(
                        f"Warning: Could not extract UIDs from add response: {e}"
                    )
                    self.selected_queue_item_uids = []

                self._refresh_queue()
                self.messageChanged.emit(f"Added {len(items)} item(s) to queue")
            else:
                error_msg = response.get("msg", "Unknown error")
                self.messageChanged.emit(f"Failed to add items to queue: {error_msg}")
        except Exception as e:
            self.messageChanged.emit(f"Error adding items to queue: {e}")

    def delete_items_from_queue(self, uids):
        """Delete multiple items from the queue."""
        if not self._rem_api or not self._is_connected:
            self.messageChanged.emit("Not connected to server")
            return
        try:
            response = self._rem_api.item_remove_batch(uids=uids, ignore_missing=True)
            if response.get("success", False):
                # Clear selection since items were deleted
                self.selected_queue_item_uids = []
                self._refresh_queue()
                self.messageChanged.emit(f"Deleted {len(uids)} item(s) from queue")
            else:
                error_msg = response.get("msg", "Unknown error")
                self.messageChanged.emit(
                    f"Failed to delete items from queue: {error_msg}"
                )
        except Exception as e:
            self.messageChanged.emit(f"Error deleting items from queue: {e}")

    def _refresh_queue(self):
        """Refresh queue data from server."""
        try:
            response = self._rem_api.queue_get()
            if response.get("success", False):
                self._queue = response.get("items", [])
                self.queueChanged.emit(self._queue)
                # Emit selection changed after queue update is processed
                # Use QTimer to ensure queueChanged signal is processed first
                QtCore.QTimer.singleShot(0, self._emit_selection_changed)
        except Exception as e:
            self.messageChanged.emit(f"Error refreshing queue: {e}")

    def _emit_selection_changed(self):
        """Emit selection changed signal with current UIDs."""
        self.queueSelectionChanged.emit(self.selected_queue_item_uids)

    def move_queue_items(
        self, uids, pos_dest=None, before_uid=None, after_uid=None, reorder=True
    ):
        """Move a batch of queue items to a new position."""
        if not self._rem_api or not self._is_connected:
            self.messageChanged.emit("Not connected to server")
            return False
        try:
            kwargs = {"uids": uids, "reorder": reorder}
            if pos_dest is not None:
                kwargs["pos_dest"] = pos_dest
            elif before_uid is not None:
                kwargs["before_uid"] = before_uid
            elif after_uid is not None:
                kwargs["after_uid"] = after_uid
            else:
                self.messageChanged.emit("Invalid position")
                return False
            response = self._rem_api.item_move_batch(**kwargs)
            if response.get("success", False):
                # Extract UIDs from moved items in response
                try:
                    moved_items = response.get("items", [])
                    if moved_items:
                        # Extract UIDs from moved items
                        moved_uids = [
                            item.get("item_uid")
                            for item in moved_items
                            if item.get("item_uid")
                        ]
                        if moved_uids:
                            # Set selected UIDs before refreshing queue
                            # This ensures queueSelectionChanged emits with correct UIDs
                            self.selected_queue_item_uids = moved_uids
                except Exception as e:
                    # If extraction fails, fall back to original UIDs
                    self.messageChanged.emit(
                        f"Warning: Could not extract UIDs from move response: {e}"
                    )
                    self.selected_queue_item_uids = uids

                self._refresh_queue()
                self.messageChanged.emit(f"Moved {len(uids)} item(s)")
                return True
            else:
                error_msg = response.get("msg", "Unknown error")
                self.messageChanged.emit(f"Failed to move items: {error_msg}")
                return False
        except Exception as e:
            self.messageChanged.emit(f"Error moving items: {e}")
            return False

    def set_queue_mode(self, loop_mode, ignore_failures=None):
        """Set queue execution mode parameters."""
        if not self._rem_api or not self._is_connected:
            self.messageChanged.emit("Not connected to server")
            return False
        try:
            if loop_mode == "default":
                mode = "default"
            else:
                mode = {"loop": loop_mode}
                if ignore_failures is not None:
                    mode["ignore_failures"] = ignore_failures
            success, msg = self._rem_api.queue_mode_set(mode=mode)
            if success:
                self.messageChanged.emit(
                    f"Queue mode set to loop = {loop_mode} ; ignore failures = {ignore_failures}"
                )
            else:
                self.messageChanged.emit(f"Failed to change the queue mode: {msg}")
            return success
        except Exception as e:
            self.messageChanged.emit(f"Error changing queue mode: {e}")
            return False

    def fetchQueue(self):
        """Fetch queue from server and update cache."""
        if not self._rem_api or not self._is_connected:
            return []
        try:
            response = self._rem_api.queue_get()
            if response.get("success", False):
                # Store in cache
                self._queue = response.get("items", [])
                # Emit signal for UI updates
                self.queueChanged.emit(self._queue)
                # Emit selection changed after queue update is processed
                QtCore.QTimer.singleShot(0, self._emit_selection_changed)
                return self._queue
            else:
                # Handle API error
                error_msg = response.get("msg", "Unknown error")
                self.messageChanged.emit(f"Failed to get queue: {error_msg}")
                return []
        except Exception as e:
            # Handle connection/API errors
            self.messageChanged.emit(f"Error getting queue: {e}")
            return []

    def clearQueue(self):
        """Clear the queue on the server."""
        if not self._rem_api or not self._is_connected:
            self.messageChanged.emit("Not connected to server")
            return False

        try:
            # Clear entire queue
            success, msg = self._rem_api.queue_clear()
            if success:
                self._queue = []
                self.queueChanged.emit([])
                self.messageChanged.emit("Queue cleared successfully")
            else:
                self.messageChanged.emit(f"Failed to clear queue: {msg}")
            return success
        except Exception as e:
            self.messageChanged.emit(f"Error clearing queue: {e}")
            return False

    def getQueue(self):
        """Get the cached queue data."""
        return self._queue.copy()

    # ========================================
    # History Methods
    # ========================================

    def fetchHistory(self):
        """Fetch history from server and update cache."""
        if not self._rem_api or not self._is_connected:
            return []
        try:
            response = self._rem_api.history_get()
            if response.get("success", False):
                # Store in cache
                self._history = response.get("items", [])
                # Emit signal for UI updates
                self.historyChanged.emit(self._history)
                return self._history
            else:
                # Handle API error
                error_msg = response.get("msg", "Unknown error")
                self.messageChanged.emit(f"Failed to get history: {error_msg}")
                return []
        except Exception as e:
            # Handle connection/API errors
            self.messageChanged.emit(f"Error getting history: {e}")
            return []

    def clearHistory(self):
        """Clear the queue history on the server."""
        if not self._rem_api or not self._is_connected:
            self.messageChanged.emit("Not connected to server")
            return False

        try:
            # Clear entire history
            success, msg = self._rem_api.history_clear()
            if success:
                self._history = []
                self.historyChanged.emit([])
                self.selected_queue_item_uids = []
                self.messageChanged.emit("History cleared successfully")
            else:
                self.messageChanged.emit(f"Failed to clear history: {msg}")
            return success
        except Exception as e:
            self.messageChanged.emit(f"Error clearing history: {e}")
            return False

    def getHistory(self):
        """Get the cached history data."""
        return self._history.copy()

    # ========================================
    # Running Plan Methods
    # ========================================

    def getRunningItem(self):
        """
        Get information about the currently running plan.

        Returns:
            dict: Running item information, empty dict if no plan is running
        """
        if not self._rem_api or not self._is_connected:
            return {}

        try:
            response = self._rem_api.queue_get()
            if response.get("success", False):
                return response.get("running_item", {})
            return {}
        except Exception:
            return {}

    def getRunList(self):
        """
        Get the list of runs associated with the currently running plan.

        Returns:
            list: List of run information dictionaries
        """
        if not self._rem_api or not self._is_connected:
            return []

        try:
            response = self._rem_api.re_runs()
            if response.get("success", False):
                return response.get("run_list", [])
            return []
        except Exception:
            return []

    # ========================================
    # Console Methods
    # ========================================

    def start_console_output_monitoring(self):
        """Enable console output monitoring."""
        self._stop_console_monitor = False
        if self._rem_api:
            self._rem_api.console_monitor.enable()

    def stop_console_output_monitoring(self):
        """Disable console output monitoring."""
        self._stop_console_monitor = True
        if self._rem_api:
            self._rem_api.console_monitor.disable()

    def console_monitoring_thread(self):
        """
        Get the next console message from the server.
        This method is designed to be called repeatedly in a background thread.

        Returns:
            tuple: (time, msg) if message received, (None, "") if timeout
        """
        if not self._rem_api or self._stop_console_monitor:
            return None, ""

        try:
            # Wait up to 0.2 seconds for a message
            payload = self._rem_api.console_monitor.next_msg(timeout=0.2)
            time = payload.get("time", None)
            msg = payload.get("msg", "")
            return time, msg
        except Exception:
            # Timeout or other error - just return empty
            return None, ""
