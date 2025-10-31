import os

import psycopg2
from dotenv import load_dotenv


class SQLConnection:
    """
    A class that contains the logic for creating a connection to the postgres database
    """
    def __init__(self):
        load_dotenv('/Users/fastcheetah/PycharmProjects/MarketSent/.env')
        try:
            self.conn = psycopg2.connect(host="localhost", dbname="postgres", user=os.getenv('DB_USERNAME'), password=os.getenv('DB_PW'), port="5432")
            self.cursor = self.conn.cursor()
        except psycopg2.Error as e:
            raise ConnectionError(f"Couldn't connect to PostgreSQL at {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.cursor.close()
        self.conn.close()
