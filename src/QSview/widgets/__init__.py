# src/QSview/widgets/__init__.py
"""
Widget components for QSview application.
"""

from .console import ConsoleWidget
from .history import HistoryWidget
from .plan_editor import PlanEditorWidget
from .queue_editor import QueueEditorWidget
from .running_plan import RunningPlanWidget
from .status import StatusWidget

__all__ = [
    "StatusWidget",
    "PlanEditorWidget",
    "QueueEditorWidget",
    "HistoryWidget",
    "ConsoleWidget",
    "RunningPlanWidget",
]
