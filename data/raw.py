from pathlib import Path

import psycopg2
import requests
from dotenv import load_dotenv
import os

envpath = Path('.', '.env')
load_dotenv('/Users/fastcheetah/PycharmProjects/MarketSent/.env')

API_KEY = os.getenv('API_KEY')
auth = requests.auth.HTTPBasicAuth(os.getenv('CLIENT_ID'), API_KEY)

api_key = os.getenv('REDDIT_PW')
print(f"getenv result: {api_key}")

credentials = {
    'grant_type' : 'password',
    'username' : os.getenv('USER'),
    'password' : os.getenv('REDDIT_PW')
}
print(os.environ)
print(credentials)

version = {'User-Agent', 'MarketSent_v0.0.1'}

res = requests.post('https://www.reddit.com/api/v1/access_token', data=credentials, auth=auth)
print(res.json())
token = res.json()['access_token']
print(token)

conn = psycopg2.connect(host="localhost", dbname = "postgres", user = "postgres", password = "ils&s!poJke5", port = "5432")


cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS post(
    id SERIAL PRIMARY KEY,
    text TEXT,
    ticker varchar(10),
    sentiment varchar(10),
    score FLOAT,
    creation DATE
);
""")

    
cur.execute("""SELECT * FROM post where SCORE > 1;""")

print(cur.fetchall())


conn.commit()
cur.close()
conn.close()