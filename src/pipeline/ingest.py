import os
import requests
from dotenv import load_dotenv


class RedditAPIClient:

    def __init__(self):
        '''
        Initializes the Reddit API Client and sets its access token
        '''
        load_dotenv('/Users/fastcheetah/PycharmProjects/MarketSent/.env')
        self.api_key = os.getenv('API_KEY')
        self.client_id = os.getenv('CLIENT_ID')
        self.headers = {'Authorization': f'bearer {self.api_key}'}
        auth = requests.auth.HTTPBasicAuth(self.client_id, self.api_key)
        credentials = {'grant_type' : 'client_credentials'}
        header = {'User-Agent': 'MarketSent_v0.0.1'}
        res = requests.post('https://www.reddit.com/api/v1/access_token', auth=auth, data = credentials, headers = header)
        self.access_token = res.json()['access_token']

    def get_headers(self):
        header = {'User-Agent': 'MarketSent_v0.0.1', 'Authorization': f'bearer {self.access_token}'}
        if not self.access_token:
            raise RuntimeError('No access token provided')
        return header

    def get_hot_posts(self, subreddit):
        '''
        Gets hot posts from a subreddit
        :param subreddit: The subreddit name posts are taken from
        :return: A pandas dataframe containg the title, upvote ratio, upvotes, and overall score of each post
        '''
        res = requests.get('https://oauth.reddit.com/r/' + subreddit + '/top', headers = self.get_headers())
        posts = res.json()['data']['children']

        data = {
            'titles': [post['data']['title'] for post in posts],
            'upvote_ratio': [post['data']['upvote_ratio'] for post in posts],
            'upvotes': [post['data']['ups'] for post in posts],
            'score': [post['data']['score'] for post in posts]
        }

        return pd.DataFrame(data)

    def get_hot_posts_no_amount(self, subreddit):
        '''
        Gets hot posts from a subreddit
        :param subreddit: The subreddit name posts are taken from
        :return: A pandas dataframe containg the title, upvote ratio, upvotes, and overall score of each post
        '''
        res = requests.get('https://oauth.reddit.com/r/' + subreddit + '/hot', headers = self.get_headers())
        posts = res.json()['data']['children']

        data = {
            'titles': [post['data']['title'] for post in posts],
            'upvote_ratio': [post['data']['upvote_ratio'] for post in posts],
            'upvotes': [post['data']['ups'] for post in posts],
            'score': [post['data']['score'] for post in posts]
        }

        return pd.DataFrame(data)
