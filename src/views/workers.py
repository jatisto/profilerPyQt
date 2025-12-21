"""
Async Workers for Database Operations

QThread workers to prevent UI blocking during database operations.
"""

from typing import List, Dict, Any, Optional
from PySide6.QtCore import QThread, Signal
from loguru import logger

from ..controllers import DatabaseController


class DatabaseWorker(QThread):
    """Base worker for database operations."""

    # Signals
    finished = Signal(bool, object, str)  # (success, result, message)
    error = Signal(str)
    progress = Signal(int)  # Progress percentage

    def __init__(self, controller: DatabaseController):
        """
        Initialize worker.

        Args:
            controller: DatabaseController instance
        """
        super().__init__()
        self.controller = controller
        self._is_running = True

    def stop(self):
        """Stop worker execution."""
        self._is_running = False


class ConnectWorker(DatabaseWorker):
    """Worker for database connection."""

    def __init__(
        self,
        controller: DatabaseController,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        ssl_mode: str = "prefer"
    ):
        """Initialize connect worker."""
        super().__init__(controller)
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.ssl_mode = ssl_mode

    def run(self):
        """Execute connection."""
        try:
            logger.info(f"Connecting to {self.database}@{self.host}:{self.port}...")
            self.progress.emit(50)

            success, message = self.controller.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                ssl_mode=self.ssl_mode
            )

            self.progress.emit(100)
            self.finished.emit(success, None, message)

        except Exception as e:
            error_msg = f"Connection error: {str(e)}"
            logger.error(error_msg)
            self.error.emit(error_msg)
            self.finished.emit(False, None, error_msg)


class QueryWorker(DatabaseWorker):
    """Worker for executing queries."""

    def __init__(self, controller: DatabaseController, query_type: str, **kwargs):
        """
        Initialize query worker.

        Args:
            controller: DatabaseController instance
            query_type: Type of query ('all', 'search', 'top20', 'table_stats')
            **kwargs: Additional arguments for specific query types
        """
        super().__init__(controller)
        self.query_type = query_type
        self.kwargs = kwargs

    def run(self):
        """Execute query based on type."""
        try:
            self.progress.emit(30)

            if self.query_type == 'all':
                success, results, message = self.controller.get_all_statements()
            elif self.query_type == 'search':
                search_text = self.kwargs.get('search_text', '')
                search_in_activity = self.kwargs.get('search_in_activity', False)
                success, results, message = self.controller.search_statements(
                    search_text,
                    search_in_activity
                )

            elif self.query_type == 'top20':
                success, results, message = self.controller.get_top_20_queries()

            elif self.query_type == 'table_stats':
                table_names = self.kwargs.get('table_names', [])
                success, results, message = self.controller.get_table_statistics(table_names)

            else:
                raise ValueError(f"Unknown query type: {self.query_type}")

            self.progress.emit(100)
            self.finished.emit(success, results, message)

        except Exception as e:
            error_msg = f"Query error: {str(e)}"
            logger.error(error_msg)
            self.error.emit(error_msg)
            self.finished.emit(False, [], error_msg)


class ResetStatsWorker(DatabaseWorker):
    """Worker for resetting statistics."""

    def __init__(self, controller: DatabaseController, reset_type: str):
        """
        Initialize reset worker.

        Args:
            controller: DatabaseController instance
            reset_type: Type of reset ('statements' or 'global')
        """
        super().__init__(controller)
        self.reset_type = reset_type

    def run(self):
        """Execute reset operation."""
        try:
            self.progress.emit(50)

            if self.reset_type == 'statements':
                success, message = self.controller.reset_pg_stat_statements()
            elif self.reset_type == 'global':
                success, message = self.controller.reset_pg_stat()
            else:
                raise ValueError(f"Unknown reset type: {self.reset_type}")

            self.progress.emit(100)
            self.finished.emit(success, None, message)

        except Exception as e:
            error_msg = f"Reset error: {str(e)}"
            logger.error(error_msg)
            self.error.emit(error_msg)
            self.finished.emit(False, None, error_msg)
