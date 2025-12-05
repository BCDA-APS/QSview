# src/QSview/widgets/__init__.py
"""
Widget components for QSview application.
"""

from .console import ConsoleWidget
from .history import HistoryWidget
from .plan_editor import PlanEditorDialog
from .queue_editor import QueueEditorWidget
from .running_plan import RunningPlanWidget
from .status import StatusWidget

__all__ = [
    "StatusWidget",
    "PlanEditorDialog",
    "QueueEditorWidget",
    "HistoryWidget",
    "ConsoleWidget",
    "RunningPlanWidget",
]
