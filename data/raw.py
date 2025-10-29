import os

import pandas
import pandas as pd
import requests
from dotenv import load_dotenv

from src.pipeline.ingest import RedditAPIClient


def main():
    client = RedditAPIClient()
    print(client.get_hot_posts(subreddit='wallstreetbets'))

if __name__ == '__main__':
    main()