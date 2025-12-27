import os

import psycopg2
from dotenv import load_dotenv

# Load .env file if it exists (for local development)
load_dotenv()


class SQLConnection:
    """
    A class that contains the logic for creating a connection to the postgres database
    """
    def __init__(self):
        try:
            # Use connection string if available (production), otherwise use individual params (local)
            connection_string = os.getenv('DB_CONNECTION_STRING')

            if connection_string:
                self.conn = psycopg2.connect(connection_string)
            else:
                # Fallback to individual parameters for local development
                self.conn = psycopg2.connect(
                    host=os.getenv('DB_HOST', 'localhost'),
                    dbname=os.getenv('DB_NAME', 'postgres'),
                    user=os.getenv('DB_USERNAME'),
                    password=os.getenv('DB_PW'),
                    port=os.getenv('DB_PORT', '5432')
                )
            self.cursor = self.conn.cursor()
        except psycopg2.Error as e:
            raise ConnectionError(f"Couldn't connect to PostgreSQL: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.cursor.close()
        self.conn.close()
