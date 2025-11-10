"""Custom table view for queue items with drag-and-drop helpers."""

import json

from PyQt5 import QtCore, QtGui, QtWidgets


class QueueTableView(QtWidgets.QTableView):
    """Table view supporting UID-based drag-and-drop reordering."""

    mime_type = "application/x-qsqueue-uids"

    def __init__(self, parent=None):
        """Initialise the table view and helper callbacks."""

        super().__init__(parent)
        self._get_uid_for_row = None
        self._move_items = None
        # leave drag/drop settings to the .ui if you like

    def set_helpers(self, *, get_uid_for_row, move_items):
        """Inject callbacks for resolving row UIDs and executing moves."""

        self._get_uid_for_row = get_uid_for_row
        self._move_items = move_items

    # ---------- drag start -------------------------------------------------
    def startDrag(self, supported_actions):  # noqa: D401 - Qt signature
        """Begin a drag operation containing the selected row UIDs."""

        if self._get_uid_for_row is None:
            return
        selected = self.selectionModel().selectedRows()
        if not selected:
            return

        uids = []
        for index in selected:
            uid = self._get_uid_for_row(index.row())
            if uid:
                uids.append(uid)
        if not uids:
            return

        mime = QtCore.QMimeData()
        payload = json.dumps(uids).encode("utf-8")
        mime.setData(self.mime_type, payload)

        drag = QtGui.QDrag(self)
        drag.setMimeData(mime)
        drag.exec_(QtCore.Qt.MoveAction)

    def dragEnterEvent(self, event):
        """Accept drags that carry the queue UID mime type."""

        if event.mimeData().hasFormat(self.mime_type):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """Allow mime payloads matching the queue UID type to move."""

        if event.mimeData().hasFormat(self.mime_type):
            event.acceptProposedAction()
        else:
            event.ignore()

    # ---------- drop -------------------------------------------------------
    def dropEvent(self, event):
        """Resolve the drop position and invoke the move callback."""

        if self._move_items is None or self._get_uid_for_row is None:
            event.ignore()
            return

        mime = event.mimeData()
        if not mime.hasFormat(self.mime_type):
            event.ignore()
            return

        try:
            uids = json.loads(bytes(mime.data(self.mime_type)).decode("utf-8"))
        except (ValueError, TypeError):
            event.ignore()
            return
        if not uids:
            event.ignore()
            return

        model = self.model()
        if model is None:
            event.ignore()
            return

        drop_index = self.indexAt(event.pos())
        before_uid = after_uid = pos_dest = None

        if not drop_index.isValid():
            pos_dest = "back"
        else:
            row = drop_index.row()
            rect = self.visualRect(drop_index)
            drop_above = event.pos().y() < rect.center().y()

            if row == 0 and drop_above:
                pos_dest = "front"
            else:
                target_uid = self._get_uid_for_row(row)
                if target_uid is None:
                    event.ignore()
                    return
                if drop_above:
                    before_uid = target_uid
                else:
                    after_uid = target_uid

        # no destination computed
        if not any((pos_dest, before_uid, after_uid)):
            event.ignore()
            return

        moved = self._move_items(
            uids=uids,
            pos_dest=pos_dest,
            before_uid=before_uid,
            after_uid=after_uid,
            reorder=True,
        )

        if moved:
            event.acceptProposedAction()
        else:
            event.ignore()
