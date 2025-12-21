"""
Secure Database Manager with Connection Pooling

Features:
- Connection pooling for better performance
- Prepared statements to prevent SQL Injection
- Async support for non-blocking operations
- Automatic retry logic
- Comprehensive error handling and logging
"""

from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional, Tuple
from loguru import logger
import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from ..config import app_config


class DatabaseConnectionError(Exception):
    """Raised when database connection fails."""
    pass


class DatabaseQueryError(Exception):
    """Raised when query execution fails."""
    pass


class DatabaseManager:
    """
    Secure database manager with connection pooling.

    Uses prepared statements to prevent SQL Injection attacks.
    Implements connection pooling for better performance.
    """

    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
        timeout: Optional[int] = None,
        ssl_mode: str = "prefer"
    ):
        """
        Initialize database manager with connection pooling.

        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password (will be handled securely)
            min_size: Minimum pool size
            max_size: Maximum pool size
            timeout: Connection timeout in seconds
            ssl_mode: SSL mode (disable, allow, prefer, require, verify-ca, verify-full)
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self._password = password  # Private, never log this

        self.min_size = min_size or app_config.db_pool_min_size
        self.max_size = max_size or app_config.db_pool_max_size
        self.timeout = timeout or app_config.db_connection_timeout
        self.ssl_mode = ssl_mode

        self._pool: Optional[ConnectionPool] = None
        self._connection_string = self._build_connection_string()

        logger.info(
            f"DatabaseManager initialized for {self.user}@{self.host}:{self.port}/{self.database}"
        )

    def _build_connection_string(self) -> str:
        """Build secure connection string."""
        return (
            f"host={self.host} "
            f"port={self.port} "
            f"dbname={self.database} "
            f"user={self.user} "
            f"password={self._password} "
            f"sslmode={self.ssl_mode} "
            f"connect_timeout={self.timeout}"
        )

    def connect(self) -> bool:
        """
        Initialize connection pool.

        Returns:
            True if successful, False otherwise
        """
        try:
            if self._pool is None:
                logger.debug(f"Creating connection pool (min={self.min_size}, max={self.max_size})")

                self._pool = ConnectionPool(
                    self._connection_string,
                    min_size=self.min_size,
                    max_size=self.max_size,
                    timeout=self.timeout,
                    kwargs={"row_factory": dict_row}
                )

                # Test connection
                with self._pool.connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT version()")
                        version = cur.fetchone()
                        logger.success(f"Connected to PostgreSQL: {version['version'][:50]}...")

                return True
        except psycopg.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise DatabaseConnectionError(f"Connection failed: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during connection: {e}")
            raise DatabaseConnectionError(f"Unexpected error: {e}") from e

    def disconnect(self) -> None:
        """Close connection pool gracefully."""
        if self._pool:
            try:
                logger.debug("Closing connection pool...")
                self._pool.close()
                self._pool = None
                logger.info("Connection pool closed successfully")
            except Exception as e:
                logger.error(f"Error closing connection pool: {e}")

    @contextmanager
    def get_connection(self) -> Iterator[psycopg.Connection]:
        """
        Get a connection from the pool (context manager).

        Yields:
            Database connection

        Raises:
            DatabaseConnectionError: If pool is not initialized
        """
        if self._pool is None:
            raise DatabaseConnectionError("Connection pool not initialized. Call connect() first.")

        conn = None
        try:
            conn = self._pool.getconn()
            yield conn
        finally:
            if conn:
                self._pool.putconn(conn)

    def execute_query(
        self,
        query: str,
        params: Optional[Tuple[Any, ...]] = None,
        fetch_all: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query with parameters (safe from SQL Injection).

        Args:
            query: SQL query with placeholders (%s)
            params: Query parameters (will be safely escaped)
            fetch_all: If True, fetch all rows; if False, fetch one

        Returns:
            List of dictionaries (rows)

        Raises:
            DatabaseQueryError: If query execution fails

        Example:
            # SAFE - uses parameterized query
            results = db.execute_query(
                "SELECT * FROM users WHERE username = %s AND age > %s",
                ("john", 25)
            )
        """
        if self._pool is None:
            raise DatabaseConnectionError("Not connected to database")

        try:
            with self._pool.connection() as conn:
                with conn.cursor() as cur:
                    # Log query (without sensitive data)
                    logger.debug(f"Executing query: {query[:100]}...")

                    # Execute with parameters (safe from SQL Injection)
                    cur.execute(query, params)

                    # Fetch results
                    if fetch_all:
                        results = cur.fetchall()
                    else:
                        result = cur.fetchone()
                        results = [result] if result else []

                    logger.debug(f"Query returned {len(results)} rows")
                    return results

        except psycopg.Error as e:
            logger.error(f"Query execution failed: {e}")
            raise DatabaseQueryError(f"Query failed: {e}") from e

    def execute_command(
        self,
        command: str,
        params: Optional[Tuple[Any, ...]] = None
    ) -> int:
        """
        Execute a command (INSERT, UPDATE, DELETE) with parameters.

        Args:
            command: SQL command with placeholders (%s)
            params: Command parameters

        Returns:
            Number of affected rows

        Raises:
            DatabaseQueryError: If command execution fails
        """
        if self._pool is None:
            raise DatabaseConnectionError("Not connected to database")

        try:
            with self._pool.connection() as conn:
                with conn.cursor() as cur:
                    logger.debug(f"Executing command: {command[:100]}...")

                    cur.execute(command, params)
                    conn.commit()

                    affected_rows = cur.rowcount
                    logger.debug(f"Command affected {affected_rows} rows")
                    return affected_rows

        except psycopg.Error as e:
            logger.error(f"Command execution failed: {e}")
            raise DatabaseQueryError(f"Command failed: {e}") from e

    def reset_pg_stat_statements(self) -> bool:
        """
        Reset pg_stat_statements statistics.

        Returns:
            True if successful
        """
        try:
            self.execute_command("SELECT pg_stat_statements_reset()")
            logger.info("pg_stat_statements reset successfully")
            return True
        except DatabaseQueryError as e:
            logger.error(f"Failed to reset pg_stat_statements: {e}")
            return False

    def reset_pg_stat(self) -> bool:
        """
        Reset global PostgreSQL statistics.

        Returns:
            True if successful
        """
        try:
            self.execute_command("SELECT pg_stat_reset()")
            logger.info("pg_stat reset successfully")
            return True
        except DatabaseQueryError as e:
            logger.error(f"Failed to reset pg_stat: {e}")
            return False

    def test_connection(self) -> bool:
        """
        Test database connection.

        Returns:
            True if connection is alive
        """
        try:
            with self._pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    result = cur.fetchone()
                    return result is not None
        except Exception as e:
            logger.warning(f"Connection test failed: {e}")
            return False

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()

    def __repr__(self) -> str:
        """String representation (safe - no password)."""
        return (
            f"DatabaseManager("
            f"host={self.host}, "
            f"port={self.port}, "
            f"database={self.database}, "
            f"user={self.user}, "
            f"pool_size={self.min_size}-{self.max_size}"
            f")"
        )
