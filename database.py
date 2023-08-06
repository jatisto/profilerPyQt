import psycopg2
from utility_function import handle_errors, write_log


@handle_errors(log_file="db.log", text='DatabaseManager')
class DatabaseManager:
    def __init__(self, dbname, host, port, username, password):
        self.dbname = dbname
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.db_connection = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()

    def connect(self):
        try:
            self.db_connection = psycopg2.connect(
                dbname=self.dbname, user=self.username, password=self.password, host=self.host, port=self.port
            )
            return True
        except Exception as e:
            write_log(f"{e}")
            return False

    def disconnect(self):
        if self.db_connection:
            self.db_connection.close()
            self.db_connection = None

    def run_execute_query(self, query):
        try:
            cursor = self.db_connection.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            write_log(f"{e}")
            return []

    def reset_stats(self):
        query = "SELECT pg_stat_statements_reset();"
        try:
            cursor = self.db_connection.cursor()
            cursor.execute(query)
            self.db_connection.commit()
            return True
        except Exception as e:
            write_log(f"{e}")
            return False
