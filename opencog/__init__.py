"""
OpenCog Multi-Agent Orchestration Workbench

A sophisticated system for autonomous multi-agent orchestration of LLM reasoning tasks,
featuring Agent-Zero as master builder and a living pattern language library.
"""

from .workbench import OpenCogWorkbench
from .agents.agent_zero import AgentZero, Agent, Task, AgentRole
from .patterns.pattern_library import PatternLanguageLibrary, CognitivePattern, PatternCategory
from .orchestration.multi_agent import Orchestrator, AgentCoordinator
from .strategies.strategy_system import StrategyRepository, Strategy, StrategyExecutor

__version__ = "1.0.0"
__all__ = [
    "OpenCogWorkbench",
    "AgentZero",
    "Agent",
    "Task",
    "AgentRole",
    "PatternLanguageLibrary",
    "CognitivePattern",
    "PatternCategory",
    "Orchestrator",
    "AgentCoordinator",
    "StrategyRepository",
    "Strategy",
    "StrategyExecutor"
]
