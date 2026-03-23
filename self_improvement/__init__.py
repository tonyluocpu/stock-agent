"""
Self-Improvement System
========================

Automatically analyzes conversations and improves the codebase.
"""

from .conversation_logger import ConversationLogger
from .session_tracker import SessionTracker
from .conversation_analyzer import ConversationAnalyzer
from .improvement_generator import ImprovementGenerator
from .test_runner import TestRunner
from .improvement_applier import ImprovementApplier
from .improvement_pipeline import ImprovementPipeline

__all__ = [
    'ConversationLogger',
    'SessionTracker',
    'ConversationAnalyzer',
    'ImprovementGenerator',
    'TestRunner',
    'ImprovementApplier',
    'ImprovementPipeline'
]

