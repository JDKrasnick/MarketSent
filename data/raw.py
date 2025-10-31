import os

import pandas
import pandas as pd
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine

from db.connection import SQLConnection
from src.pipeline.ingest import RedditAPIClient

class RawDataIngestor:
    '''
    The class that retreives API data and inserts the raw form into the database
    '''


    def __init__(self):
        self.api = RedditAPIClient()
        self.subreddit = 'wallstreetbets'

    def add_last_day(self, amount, db):
        """
        Effect: Adds ``amount`` of posts into the database, taken from the last day. Posts are added sorted by "top"
        :param db: The name of the database to add it to
        """
        df = self.api.get_posts_daily(self.subreddit, amount)
        return df
        df.to_sql(db, self.engine, if_exists='append', index=False)


    def add_last_week(self, amount, db):
        '''
        Returns: A dataframe containing ``amount`` posts from the given subreddit. Posts are given sorted by "top"
        :param db: The name of the database to add it to
        '''
        df = self.api.get_posts_weekly(self.subreddit, amount)
        return df


if __name__ == '__main__':
    ingestor = RawDataIngestor()
    ingestor.add_last_day(100, 'posts')
