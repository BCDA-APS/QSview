"""
Support functions for this demo project.

.. autosummary::

    ~myLoadUi
    ~getUiFileName
    ~reconnect
    ~debug_signal
"""

import pathlib


MAX_LENGTH_COLUMN_QUEUE_STATIC = 750
MAX_LENGTH_COLUMN_QUEUE_DYNAMIC = 250
MAX_LENGTH_COLUMN_HISTORY_STATIC = 500
MAX_LENGTH_COLUMN_HISTORY_DYNAMIC = 250


def myLoadUi(ui_file, baseinstance=None, **kw):
    """
    Load a .ui file for use in building a GUI.

    Wraps `uic.loadUi()` with code that finds our program's
    *resources* directory.

    :see: http://nullege.com/codes/search/PyQt4.uic.loadUi
    :see: http://bitesofcode.blogspot.ca/2011/10/comparison-of-loading-techniques.html

    inspired by:
    http://stackoverflow.com/questions/14892713/how-do-you-load-ui-files-onto-python-classes-with-pyside?lq=1
    """
    from PyQt5 import uic

    from . import UI_DIR

    if isinstance(ui_file, str):
        ui_file = UI_DIR / ui_file

    # print(f"myLoadUi({ui_file=})")
    return uic.loadUi(ui_file, baseinstance=baseinstance, **kw)


def getUiFileName(py_file_name):
    """UI file name matches the Python file, different extension."""
    return f"{pathlib.Path(py_file_name).stem}.ui"


def reconnect(signal, new_slot):
    """
    Disconnects any slots connected to the given signal and then connects the signal to the new_slot.

    Parameters:
        - signal: The signal to disconnect and then reconnect.
        - new_slot: The new slot to connect to the signal.

    Note:
        - this function catches TypeError which occurs if the signal was not connected to any slots.
    """
    try:
        signal.disconnect()
    except TypeError:
        pass
    signal.connect(new_slot)


def debug_signal(*args, **kwargs):
    """Print statement when a signal is emitted."""
    print("\nSignal emitted with args:", args, "and kwargs:", kwargs)


def truncate_preview(text: str, max_length: int) -> str:
    return text[:max_length] + "…" if len(text) > max_length else text


def format_kwargs_three_lines(kwargs: dict) -> str:
    lines = []
    if not kwargs:
        return ""
    if "detectors" in kwargs:
        lines.append(f"detectors = {kwargs['detectors']}")
    other_kwargs = {k: v for k, v in kwargs.items() if k not in ["detectors", "md"]}
    if other_kwargs:
        lines.append(f"args = {other_kwargs}")
    if "md" in kwargs:
        lines.append(f"md = {kwargs['md']}")
    return "\n".join(lines)


def resize_table_with_caps(table_view, max_length):
    """Resize table after data is loaded with column cap."""
    if not table_view.model():
        return

    table_view.resizeColumnsToContents()
    table_view.resizeRowsToContents()

    for col in range(table_view.model().columnCount()):
        if table_view.columnWidth(col) > max_length:
            table_view.setColumnWidth(col, max_length)
