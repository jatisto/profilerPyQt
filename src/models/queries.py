"""
Secure SQL Queries Module

All queries use parameterized statements to prevent SQL Injection.
Never use f-strings or string concatenation for user input!
"""

from typing import Dict, List, Tuple, Any


class SQLQueries:
    """Collection of safe, parameterized SQL queries."""

    # Table column definitions
    COLUMNS_DEFAULT = [
        "query",
        "rows",
        "calls",
        "total_exec_time",
        "shared_blks_read",
        "shared_blks_written",
        "local_blks_read",
        "local_blks_written",
        "query_start",
        "backend_start"
    ]

    COLUMNS_TABLE_STATS = [
        "table_name",
        "inserted_rows",
        "updated_rows",
        "deleted_rows",
        "seq_scans",
        "idx_scans",
        "dead_tuples",
        "", "", ""
    ]

    COLUMNS_TOP_20 = [
        "query",
        "total_time",
        "calls",
        "mean_time",
        "cpu_percentage",
        "", "", "", "", ""
    ]

    # ==================== pg_stat_statements Queries ====================

    @staticmethod
    def get_all_statements(database_name: str) -> Tuple[str, Tuple[str]]:
        """
        Get all SQL statements from pg_stat_statements.

        Args:
            database_name: Database name to filter

        Returns:
            (query, parameters) tuple

        Example:
            query, params = SQLQueries.get_all_statements("mydb")
            results = db.execute_query(query, params)
        """
        query = """
            SELECT DISTINCT
                pg.query AS query,
                pg.rows AS rows,
                pg.calls AS calls,
                pg.total_exec_time AS total_exec_time,
                pg.shared_blks_read AS shared_blks_read,
                pg.shared_blks_written AS shared_blks_written,
                pg.local_blks_read AS local_blks_read,
                pg.local_blks_written AS local_blks_written,
                pa.query_start AS query_start,
                pa.backend_start AS backend_start
            FROM pg_stat_statements pg
            JOIN pg_database db ON pg.dbid = db.oid
            JOIN pg_authid auth ON pg.userid = auth.oid
            JOIN pg_stat_activity pa ON db.oid = pa.datid AND auth.oid = pa.usesysid
            WHERE db.datname = %s
            ORDER BY pa.query_start DESC
        """
        return (query, (database_name,))

    @staticmethod
    def search_statements(
        database_name: str,
        search_pattern: str,
        search_in_activity: bool = False
    ) -> Tuple[str, Tuple[str, str]]:
        """
        Search SQL statements by pattern.

        Args:
            database_name: Database name to filter
            search_pattern: Search pattern (will be wrapped with %)
            search_in_activity: If True, search in pg_stat_activity as well

        Returns:
            (query, parameters) tuple

        Security Note:
            User input is safely passed as a parameter, not concatenated!
        """
        # Wrap search pattern with % for LIKE operator
        like_pattern = f"%{search_pattern}%"

        if search_in_activity:
            search_condition = "pg.query LIKE %s OR pa.query LIKE %s"
            params = (database_name, like_pattern, like_pattern)
        else:
            search_condition = "pg.query LIKE %s"
            params = (database_name, like_pattern)

        query = f"""
            SELECT DISTINCT
                pg.query AS query,
                pg.rows AS rows,
                pg.calls AS calls,
                pg.total_exec_time AS total_exec_time,
                pg.shared_blks_read AS shared_blks_read,
                pg.shared_blks_written AS shared_blks_written,
                pg.local_blks_read AS local_blks_read,
                pg.local_blks_written AS local_blks_written,
                pa.query_start AS query_start,
                pa.backend_start AS backend_start
            FROM pg_stat_statements pg
            JOIN pg_database db ON pg.dbid = db.oid
            JOIN pg_authid auth ON pg.userid = auth.oid
            JOIN pg_stat_activity pa ON db.oid = pa.datid AND auth.oid = pa.usesysid
            WHERE db.datname = %s AND ({search_condition})
            ORDER BY pa.query_start DESC
        """
        return (query, params)

    @staticmethod
    def get_top_20_queries(database_name: str) -> Tuple[str, Tuple[str]]:
        """
        Get top 20 most resource-intensive queries.

        Args:
            database_name: Database name to filter

        Returns:
            (query, parameters) tuple
        """
        query = """
            SELECT
                query AS query,
                ROUND(pg.total_exec_time::numeric, 2) AS total_time,
                calls AS calls,
                ROUND(pg.mean_exec_time::numeric, 2) AS mean_time,
                ROUND(
                    (100 * pg.total_exec_time /
                     NULLIF(SUM(pg.total_exec_time::numeric) OVER (), 0)
                    )::numeric, 2
                ) AS cpu_percentage
            FROM pg_stat_statements pg
            JOIN pg_database db ON pg.dbid = db.oid
            WHERE db.datname = %s
            ORDER BY total_time DESC
            LIMIT 20
        """
        return (query, (database_name,))

    # ==================== pg_stat_user_tables Queries ====================

    @staticmethod
    def get_table_statistics(table_names: List[str]) -> Tuple[str, Tuple[str, ...]]:
        """
        Get INSERT/UPDATE/DELETE statistics for specific tables.

        Args:
            table_names: List of table names to query

        Returns:
            (query, parameters) tuple

        Security Note:
            Table names are passed as parameters using ANY(%s) with array.
        """
        query = """
            SELECT
                relname AS table_name,
                n_tup_ins AS inserted_rows,
                n_tup_upd AS updated_rows,
                n_tup_del AS deleted_rows,
                seq_scan AS seq_scans,
                idx_scan AS idx_scans,
                n_dead_tup AS dead_tuples
            FROM pg_stat_user_tables
            WHERE relname = ANY(%s)
            ORDER BY n_tup_ins DESC
        """
        # Convert list to tuple for psycopg3
        return (query, (table_names,))

    @staticmethod
    def get_all_table_statistics() -> Tuple[str, Tuple]:
        """
        Get statistics for all user tables.

        Returns:
            (query, parameters) tuple
        """
        query = """
            SELECT
                relname AS table_name,
                n_tup_ins AS inserted_rows,
                n_tup_upd AS updated_rows,
                n_tup_del AS deleted_rows,
                seq_scan AS seq_scans,
                idx_scan AS idx_scans,
                n_dead_tup AS dead_tuples
            FROM pg_stat_user_tables
            ORDER BY n_tup_ins DESC
        """
        return (query, ())

    # ==================== Utility Queries ====================

    @staticmethod
    def get_database_size(database_name: str) -> Tuple[str, Tuple[str]]:
        """
        Get database size in human-readable format.

        Args:
            database_name: Database name

        Returns:
            (query, parameters) tuple
        """
        query = """
            SELECT pg_size_pretty(pg_database_size(%s)) AS size
        """
        return (query, (database_name,))

    @staticmethod
    def get_active_connections(database_name: str) -> Tuple[str, Tuple[str]]:
        """
        Get count of active connections to database.

        Args:
            database_name: Database name

        Returns:
            (query, parameters) tuple
        """
        query = """
            SELECT COUNT(*) AS connection_count
            FROM pg_stat_activity
            WHERE datname = %s
        """
        return (query, (database_name,))

    @staticmethod
    def get_slow_queries(
        database_name: str,
        min_duration_ms: float = 1000.0
    ) -> Tuple[str, Tuple[str, float]]:
        """
        Get queries that took longer than specified duration.

        Args:
            database_name: Database name
            min_duration_ms: Minimum duration in milliseconds

        Returns:
            (query, parameters) tuple
        """
        query = """
            SELECT
                query,
                calls,
                ROUND(mean_exec_time::numeric, 2) AS mean_time_ms,
                ROUND(max_exec_time::numeric, 2) AS max_time_ms
            FROM pg_stat_statements pg
            JOIN pg_database db ON pg.dbid = db.oid
            WHERE db.datname = %s
              AND mean_exec_time > %s
            ORDER BY mean_exec_time DESC
        """
        return (query, (database_name, min_duration_ms))

    @staticmethod
    def get_table_bloat() -> Tuple[str, Tuple]:
        """
        Estimate table bloat (dead tuples).

        Returns:
            (query, parameters) tuple
        """
        query = """
            SELECT
                schemaname,
                tablename,
                n_dead_tup AS dead_tuples,
                n_live_tup AS live_tuples,
                ROUND(
                    100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0),
                    2
                ) AS bloat_percentage
            FROM pg_stat_user_tables
            WHERE n_dead_tup > 0
            ORDER BY n_dead_tup DESC
            LIMIT 20
        """
        return (query, ())


def validate_table_names(table_names: List[str]) -> List[str]:
    """
    Validate and sanitize table names.

    Args:
        table_names: List of table names from user input

    Returns:
        Cleaned list of table names

    Raises:
        ValueError: If any table name contains invalid characters
    """
    import re

    cleaned_names = []
    # PostgreSQL identifier pattern: alphanumeric, underscore, up to 63 chars
    pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]{0,62}$')

    for name in table_names:
        name = name.strip().strip("'\"")
        if not name:
            continue

        if not pattern.match(name):
            raise ValueError(
                f"Invalid table name: '{name}'. "
                f"Must start with letter/underscore and contain only alphanumeric/underscore."
            )

        cleaned_names.append(name)

    return cleaned_names
