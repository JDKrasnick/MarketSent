import os
import re
import pandas as pd

from dotenv import load_dotenv
from sqlalchemy import create_engine


from src.pipeline.ingest import RawDataIngestor

from yahooquery import search

from src.pipeline.CompanyTickers import COMPANY_TICKERS
from src.pipeline.sentiment import SentimentPipeline


class ProcessDB():

    @staticmethod
    def ingestAndProcessDay(db):
        '''
        Runs the full data pipeline to get the last day's data and add the proceessesd version to the pipeline
        '''
        load_dotenv('/Users/fastcheetah/PycharmProjects/MarketSent/.env')
        db_connection_str = os.getenv("DB_CONNECTION_STRING")
        engine = create_engine(db_connection_str)

        ingest = RawDataIngestor()
        model = SentimentPipeline()
        raw_df = ingest.get_last_day()
        processed_df = ProcessDB.processR(raw_df, model)

        return processed_df

    @staticmethod
    def ingestAndProcessWeek(db):
        '''
        Runs the full data pipeline to get the last day's data and add the proceessesd version to the pipeline
        '''
        load_dotenv('/Users/fastcheetah/PycharmProjects/MarketSent/.env')
        db_connection_str = os.getenv("DB_CONNECTION_STRING")
        engine = create_engine(db_connection_str)

        ingest = RawDataIngestor()
        model = SentimentPipeline()
        raw_df = ingest.get_last_week()
        processed_df = ProcessDB.processR(raw_df, model)

        # Insert rows one by one with conflict handling
        for _, row in processed_df.iterrows():
            try:
                row.to_frame().T.to_sql(db, engine, if_exists='append', index=False)
            except Exception as e:
                print(e)
                pass


    @staticmethod
    def processR(df, model):
        '''
        Proccesses the raw reddit data by adding the ticker and sentiment score
        '''

        df[['positive', 'negative', 'neutral']] = df.apply(
            lambda row: pd.Series(model.analyze(row['text'] + ' ' + row['post_text'])[0]),
            axis=1
        )

        return df


    @staticmethod
    def getTicker(title):
        # Remove YOLO (not a ticker lol)
        title = title.replace('YOLO', '')

        ticker_pattern = r'\b([A-Z]{2,5}(?:\.[A-Z]{1,3})?)\b'
        matches = re.findall(ticker_pattern, title)

        word_list = title.split()
        word_list = [item.lower() for item in word_list]
        for word in word_list:
            if word in COMPANY_TICKERS:
                return COMPANY_TICKERS[word]

        # Return first match that isn't AI
        for ticker in matches:
            if ticker != 'AI' and ticker != 'US' and ticker != 'CEO' and ticker != 'LOL' and ticker != 'LOVE' and ticker != 'BULL':
                return ticker

        return None

    @staticmethod
    def getTickerGivenName(title):
        '''Returns the stock ticker of a company given its name. Ex. Alphabet -> GOOG'''

        word_list = title.split()

        for word in word_list:
            try:
                name = search(title)
                possible_ticker = name.get('quotes', [])

                if possible_ticker:
                    return possible_ticker[0].get('symbol')
            except Exception as e:
                pass

        return None

if __name__ == '__main__':
    ProcessDB.ingestAndProcessWeek('posts')