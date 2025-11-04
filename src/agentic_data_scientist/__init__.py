"""
Agentic Data Scientist - A General-Purpose Multi-Agent Framework.

Agentic Data Scientist provides a clean Python API and CLI for orchestrating complex tasks
using Google's Agent Development Kit (ADK) and Claude Code CLI agents.
"""

from agentic_data_scientist.core.api import DataScientist, Result, SessionConfig


__version__ = "0.1.0"
__all__ = ["DataScientist", "Result", "SessionConfig"]
