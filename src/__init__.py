"""
PgSSR - PostgreSQL Statistics Statements Reader

Modern desktop application for monitoring and analyzing PostgreSQL query performance.
"""

__version__ = "2.0.0"
__author__ = "Your Name"
__license__ = "MIT"

from .config import app_config, db_default_config

__all__ = ["app_config", "db_default_config"]
