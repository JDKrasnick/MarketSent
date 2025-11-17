from datetime import datetime
import os

import pandas as pd
import praw
from dotenv import load_dotenv


class RedditAPIClient:

    def __init__(self):
        '''
        Initializes the Reddit API Client using PRAW
        '''
        load_dotenv('/Users/fastcheetah/PycharmProjects/MarketSent/.env')
        self.client_id = os.getenv('CLIENT_ID')
        self.client_secret = os.getenv('API_KEY')  # PRAW uses client_secret instead of API_KEY

        self.reddit = praw.Reddit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            user_agent='MarketSent_v0.0.1'
        )

    def get_top_posts(self, subreddit):
        '''
        Returns: Top 100 posts from a subreddit
        :param subreddit: The subreddit name posts are taken from
        :return: A pandas dataframe containing the title, upvote ratio, upvotes, and overall score of each post
        '''
        subreddit_obj = self.reddit.subreddit(subreddit)
        posts = subreddit_obj.top(limit=1000)

        return pd.DataFrame(posts_to_data(posts))

    def get_posts_daily(self, subreddit):
        '''
        Returns: Top 100 posts from the last day of a subreddit

        Requires: amount <= 1000

        :param subreddit: The subreddit name posts are taken from
        :return: A pandas dataframe containing posts from the last day
        '''
        subreddit_obj = self.reddit.subreddit(subreddit)
        posts = subreddit_obj.top(time_filter='day', limit=1000)

        return pd.DataFrame(posts_to_data(posts))

    def get_posts_weekly(self, subreddit):
        '''
        Returns: Top 100 posts from the last week of a subreddit

        Requires: amount <= 1000

        :param subreddit: The subreddit name posts are taken from
        :return: A pandas dataframe containing posts from the last day
        '''
        subreddit_obj = self.reddit.subreddit(subreddit)
        posts = subreddit_obj.top(time_filter='week', limit=1000)


        return pd.DataFrame(posts_to_data(posts))


def posts_to_data(posts):
    '''
    Converts PRAW submission objects to a dictionary for DataFrame creation
    :return: Dictionary with post data
    '''
    data = {
        'text': [],
        'upvote_ratio': [],
        'score': [],
        'creation': [],
        'ticker': [],
        'positive': [],
        'negative': [],
        'neutral': [],
    }

    for post in posts:
        data['text'].append(post.title)
        data['upvote_ratio'].append(post.upvote_ratio)
        data['score'].append(post.score)
        data['creation'].append(datetime.fromtimestamp(post.created_utc))
        data['ticker'].append(None)
        data['positive'].append(None)
        data['negative'].append(None)
        data['neutral'].append(None)

    return data