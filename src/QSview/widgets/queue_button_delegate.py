"""
Button Delegate for Queue Table - handles Edit/Delete buttons in cells.
"""

from PyQt5 import QtCore, QtGui, QtWidgets


class ButtonDelegate(QtWidgets.QStyledItemDelegate):
    """Delegate for rendering buttons in table cells."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.button_margin = 2
        self.button_height = 30
        self.button_width = 40

    def paint(self, painter, option, index):
        """Paint the button in the cell."""

        # Set up button appearance
        button_rect = self._get_button_rect(option.rect)

        # Button background (light gray)
        painter.fillRect(button_rect, QtGui.QColor(240, 240, 240))

        # Button border
        pen = QtGui.QPen(QtGui.QColor(200, 200, 200))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawRoundedRect(button_rect, 3, 3)

        # Draw icon
        icon = QtGui.QIcon(
            ":/icons/edit.png" if self._is_edit_column(index) else ":/icons/delete.png"
        )
        icon_size = QtCore.QSize(16, 16)
        icon_rect = QtCore.QRect(
            button_rect.center().x() - icon_size.width() // 2,
            button_rect.center().y() - icon_size.height() // 2,
            icon_size.width(),
            icon_size.height(),
        )
        icon.paint(painter, icon_rect, QtCore.Qt.AlignCenter)

    def sizeHint(self, option, index):
        """Return the size hint for the button."""
        return QtCore.QSize(self.button_width, self.button_height)

    def editorEvent(self, event, model, option, index):
        """Handle mouse events (clicks) on the button."""
        if event.type() == QtCore.QEvent.MouseButtonPress:
            if self._is_button_clicked(event.pos(), option.rect):
                # Emit a signal or call a callback
                self.button_clicked.emit(index.row(), self._is_edit_column(index))
                return True
        return super().editorEvent(event, model, option, index)

    def _get_button_rect(self, cell_rect):
        """Calculate button rectangle within cell."""
        # Center the button horizontally and vertically
        button_x = cell_rect.left() + (cell_rect.width() - self.button_width) // 2
        button_y = cell_rect.top() + (cell_rect.height() - self.button_height) // 2
        return QtCore.QRect(
            button_x,
            button_y,
            self.button_width,
            self.button_height,
        )

    def _is_button_clicked(self, pos, cell_rect):
        """Check if click is within button area."""
        button_rect = self._get_button_rect(cell_rect)
        return button_rect.contains(pos)

    def _is_edit_column(self, index):
        """Check if this is the Edit column."""
        return index.column() == index.model().columnCount() - 2

    # Signal to emit when button is clicked
    button_clicked = QtCore.pyqtSignal(int, bool)  # row, is_edit
