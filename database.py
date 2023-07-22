from aifc import Error

import psycopg2
from psycopg2 import extensions


class DatabaseManager:
    def __init__(self, dbname, host, port, username, password):
        self.dbname = dbname
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.db_connection = None

    def connect(self):
        try:
            self.db_connection = psycopg2.connect(
                dbname=self.dbname, user=self.username, password=self.password, host=self.host, port=self.port
            )
            return True
        except Exception as e:
            # Handle the error and return False to indicate connection failure
            # You may also add logging for the error
            return False

    def disconnect(self):
        if self.db_connection:
            self.db_connection.close()
            self.db_connection = None

    def execute_query(self, query):
        try:
            cursor = self.db_connection.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            # Handle the error and return an empty list to indicate query execution failure
            # You may also add logging for the error
            return []

    def reset_stats(self):
        query = "SELECT pg_stat_statements_reset();"
        try:
            cursor = self.db_connection.cursor()
            cursor.execute(query)
            self.db_connection.commit()
            return True
        except Exception as e:
            # Handle the error and return False to indicate stat reset failure
            # You may also add logging for the error
            return False
