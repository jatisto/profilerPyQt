"""
Database Controller - Business Logic Layer

Separates business logic from UI layer.
Handles all database operations and query execution.
"""

from typing import List, Dict, Any, Optional, Tuple
from loguru import logger

from ..models import DatabaseManager, DatabaseConnectionError, DatabaseQueryError, SQLQueries
from ..models.queries import validate_table_names


class DatabaseController:
    """
    Controller for database operations.

    Handles the business logic for executing queries and managing database state.
    Acts as an intermediary between UI and DatabaseManager.
    """

    def __init__(self):
        """Initialize database controller."""
        self.db_manager: Optional[DatabaseManager] = None
        self.current_database: Optional[str] = None
        logger.debug("DatabaseController initialized")

    def connect(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        ssl_mode: str = "prefer"
    ) -> Tuple[bool, str]:
        """
        Connect to PostgreSQL database.

        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Username
            password: Password
            ssl_mode: SSL mode

        Returns:
            (success: bool, message: str) tuple
        """
        try:
            # Create new database manager
            self.db_manager = DatabaseManager(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
                ssl_mode=ssl_mode
            )

            # Connect
            success = self.db_manager.connect()

            if success:
                self.current_database = database
                logger.success(f"Connected to database: {database}")
                return (True, f"Successfully connected to {database}")
            else:
                return (False, "Connection failed")

        except DatabaseConnectionError as e:
            error_msg = f"Connection failed: {str(e)}"
            logger.error(error_msg)
            return (False, error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return (False, error_msg)

    def disconnect(self) -> Tuple[bool, str]:
        """
        Disconnect from database.

        Returns:
            (success: bool, message: str) tuple
        """
        try:
            if self.db_manager:
                self.db_manager.disconnect()
                self.db_manager = None
                self.current_database = None
                logger.info("Disconnected from database")
                return (True, "Disconnected successfully")
            return (True, "Already disconnected")

        except Exception as e:
            error_msg = f"Disconnect failed: {str(e)}"
            logger.error(error_msg)
            return (False, error_msg)

    def is_connected(self) -> bool:
        """
        Check if connected to database.

        Returns:
            True if connected
        """
        return self.db_manager is not None and self.db_manager.test_connection()

    def get_all_statements(self) -> Tuple[bool, List[Dict[str, Any]], str]:
        """
        Get all SQL statements from pg_stat_statements.

        Returns:
            (success: bool, results: List[Dict], message: str) tuple
        """
        if not self.is_connected():
            return (False, [], "Not connected to database")

        try:
            query, params = SQLQueries.get_all_statements(self.current_database)
            results = self.db_manager.execute_query(query, params)

            logger.info(f"Retrieved {len(results)} statements")
            return (True, results, f"Found {len(results)} statements")

        except DatabaseQueryError as e:
            error_msg = f"Query failed: {str(e)}"
            logger.error(error_msg)
            return (False, [], error_msg)

    def search_statements(
        self,
        search_text: str,
        search_in_activity: bool = False
    ) -> Tuple[bool, List[Dict[str, Any]], str]:
        """
        Search SQL statements by pattern.

        Args:
            search_text: Search pattern
            search_in_activity: Search in pg_stat_activity as well

        Returns:
            (success: bool, results: List[Dict], message: str) tuple
        """
        if not self.is_connected():
            return (False, [], "Not connected to database")

        if not search_text.strip():
            # Return all statements if search is empty
            return self.get_all_statements()

        try:
            query, params = SQLQueries.search_statements(
                self.current_database,
                search_text,
                search_in_activity
            )
            results = self.db_manager.execute_query(query, params)

            logger.info(f"Search '{search_text}' returned {len(results)} results")
            return (True, results, f"Found {len(results)} matching statements")

        except DatabaseQueryError as e:
            error_msg = f"Search failed: {str(e)}"
            logger.error(error_msg)
            return (False, [], error_msg)

    def get_top_20_queries(self) -> Tuple[bool, List[Dict[str, Any]], str]:
        """
        Get top 20 most resource-intensive queries.

        Returns:
            (success: bool, results: List[Dict], message: str) tuple
        """
        if not self.is_connected():
            return (False, [], "Not connected to database")

        try:
            query, params = SQLQueries.get_top_20_queries(self.current_database)
            results = self.db_manager.execute_query(query, params)

            logger.info(f"Retrieved top {len(results)} queries")
            return (True, results, f"Found {len(results)} top queries")

        except DatabaseQueryError as e:
            error_msg = f"Query failed: {str(e)}"
            logger.error(error_msg)
            return (False, [], error_msg)

    def get_table_statistics(
        self,
        table_names: List[str]
    ) -> Tuple[bool, List[Dict[str, Any]], str]:
        """
        Get INSERT/UPDATE/DELETE statistics for specific tables.

        Args:
            table_names: List of table names

        Returns:
            (success: bool, results: List[Dict], message: str) tuple
        """
        if not self.is_connected():
            return (False, [], "Not connected to database")

        if not table_names:
            return (False, [], "No table names provided")

        try:
            # Validate and sanitize table names
            validated_names = validate_table_names(table_names)

            if not validated_names:
                return (False, [], "All table names are invalid")

            query, params = SQLQueries.get_table_statistics(validated_names)
            results = self.db_manager.execute_query(query, params)

            logger.info(f"Retrieved statistics for {len(results)} tables")
            return (True, results, f"Found statistics for {len(results)} tables")

        except ValueError as e:
            error_msg = f"Invalid table names: {str(e)}"
            logger.error(error_msg)
            return (False, [], error_msg)
        except DatabaseQueryError as e:
            error_msg = f"Query failed: {str(e)}"
            logger.error(error_msg)
            return (False, [], error_msg)

    def reset_pg_stat_statements(self) -> Tuple[bool, str]:
        """
        Reset pg_stat_statements statistics.

        Returns:
            (success: bool, message: str) tuple
        """
        if not self.is_connected():
            return (False, "Not connected to database")

        try:
            success = self.db_manager.reset_pg_stat_statements()

            if success:
                logger.info("pg_stat_statements reset successfully")
                return (True, "Statistics reset successfully")
            else:
                return (False, "Reset failed")

        except Exception as e:
            error_msg = f"Reset failed: {str(e)}"
            logger.error(error_msg)
            return (False, error_msg)

    def reset_pg_stat(self) -> Tuple[bool, str]:
        """
        Reset global PostgreSQL statistics.

        Returns:
            (success: bool, message: str) tuple
        """
        if not self.is_connected():
            return (False, "Not connected to database")

        try:
            success = self.db_manager.reset_pg_stat()

            if success:
                logger.info("pg_stat reset successfully")
                return (True, "Global statistics reset successfully")
            else:
                return (False, "Reset failed")

        except Exception as e:
            error_msg = f"Reset failed: {str(e)}"
            logger.error(error_msg)
            return (False, error_msg)

    def get_database_size(self) -> Tuple[bool, str, str]:
        """
        Get current database size.

        Returns:
            (success: bool, size: str, message: str) tuple
        """
        if not self.is_connected():
            return (False, "", "Not connected to database")

        try:
            query, params = SQLQueries.get_database_size(self.current_database)
            results = self.db_manager.execute_query(query, params, fetch_all=False)

            if results:
                size = results[0].get('size', 'Unknown')
                return (True, size, f"Database size: {size}")
            return (False, "", "No size information available")

        except DatabaseQueryError as e:
            error_msg = f"Query failed: {str(e)}"
            logger.error(error_msg)
            return (False, "", error_msg)

    def get_active_connections(self) -> Tuple[bool, int, str]:
        """
        Get count of active connections to current database.

        Returns:
            (success: bool, count: int, message: str) tuple
        """
        if not self.is_connected():
            return (False, 0, "Not connected to database")

        try:
            query, params = SQLQueries.get_active_connections(self.current_database)
            results = self.db_manager.execute_query(query, params, fetch_all=False)

            if results:
                count = results[0].get('connection_count', 0)
                return (True, count, f"Active connections: {count}")
            return (False, 0, "No connection information available")

        except DatabaseQueryError as e:
            error_msg = f"Query failed: {str(e)}"
            logger.error(error_msg)
            return (False, 0, error_msg)
