# src/QSviz/widgets/__init__.py
"""
Widget components for QSviz application.
"""

from .console import ConsoleWidget
from .history import HistoryWidget
from .plan_editor import PlanEditorWidget
from .queue_editor import QueueEditorWidget
from .status import StatusWidget

__all__ = [
    "StatusWidget",
    "PlanEditorWidget",
    "QueueEditorWidget",
    "HistoryWidget",
    "ConsoleWidget",
]
