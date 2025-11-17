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

    def get_last_day(self):
        """
        Returns: A dataframe containing up to 1000 posts from the last day, sorted by "top"
        """
        df = self.api.get_posts_daily(self.subreddit)
        return df


    def get_last_week(self):
        """
        Returns: A dataframe containing up to 1000 posts from the last week, sorted by "top"
        """
        df = self.api.get_posts_weekly(self.subreddit)
        return df


if __name__ == '__main__':
    ingestor = RawDataIngestor()
    print(ingestor.get_last_day(100))
