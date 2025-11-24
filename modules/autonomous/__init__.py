"""
Autonomous Brain System for Heist Engine
=========================================

Self-diagnosing, self-healing AI with position sizing.
"""

from .monitor import RailwayLogMonitor
from .classifier import IssueClassifier, Severity, ApprovalLevel
from .logger import ActionLogger, BrainAction
from .github_manager import GitHubManager
from .fix_generator import AIFixGenerator
from .fix_workflow import AutonomousFixWorkflow
from .trainer import TrainingScheduler, ResearchAgent
from .approval import ApprovalSystem, KillSwitch
from .position_sizer import AdaptivePositionSizer, PositionSizingStrategy

__version__ = "1.0.0"
__all__ = [
    'RailwayLogMonitor',
    'IssueClassifier',
    'ActionLogger',
    'BrainAction',
    'Severity',
    'ApprovalLevel',
    'GitHubManager',
    'AIFixGenerator',
    'AutonomousFixWorkflow',
    'TrainingScheduler',
    'ResearchAgent',
    'ApprovalSystem',
    'KillSwitch',
    'AdaptivePositionSizer',
    'PositionSizingStrategy'
]
