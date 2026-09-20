"""
Configuration package for Project Oracle.

Re-exports the core configuration types so consumers can write::

    from src.config import Settings, ConfigurationError
"""

from src.config.settings import ConfigurationError, Settings

__all__ = ["ConfigurationError", "Settings"]
