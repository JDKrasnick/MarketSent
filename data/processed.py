import os
from abc import abstractmethod

from sqlalchemy import create_engine

from data.raw import RedditAPIClient

def Command(ABC):
    @abstractmethod
    def execute(self):
        pass

class processDB(Command):
    def __init__(self, ):
        db_connection_str = os.getenv("DB_CONNECTION_STRING")
        self.engine = create_engine(db_connection_str)
        pass

    def execute(self):
        pass

    def ingestAndProcessDay(self):
        df.to_sql(db, self.engine, if_exists='append', index=False)
        pass