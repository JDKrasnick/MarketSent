import os
import re
from abc import abstractmethod, ABC

from dotenv import load_dotenv
from sqlalchemy import create_engine

from data.raw import RedditAPIClient, RawDataIngestor


class ProcessDB():

    @staticmethod
    def ingestAndProcessDay(db, amount):
        '''
        Runs the full data pipeline to get the last day's data and add the proceessesd version to the pipeline
        '''
        load_dotenv('/Users/fastcheetah/PycharmProjects/MarketSent/.env')
        db_connection_str = os.getenv("DB_CONNECTION_STRING")
        engine = create_engine(db_connection_str)

        ingest = RawDataIngestor()
        raw_df = ingest.get_last_day(amount, db)
        processed_df = ProcessDB.processR(raw_df)

        # Insert rows one by one with conflict handling
        for _, row in processed_df.iterrows():
            try:
                row.to_frame().T.to_sql(db, engine, if_exists='append', index=False)
            except Exception:
                pass


    @staticmethod
    def processR(df):
        '''
        Proccesses the raw reddit data by adding the ticker and sentiment score
        '''

        df['ticker'] = df['text'].apply(ProcessDB.getTicker)
        print(df['ticker'].values)

        return df;

    @staticmethod
    def getTicker(title):
        # Remove YOLO (not a ticker lol)
        title = title.replace('YOLO', '')

        ticker_pattern = r'\b([A-Z]{2,5}(?:\.[A-Z]{1,3})?)\b'
        matches = re.findall(ticker_pattern, title)

        # Return first match that isn't AI
        for ticker in matches:
            if ticker != 'AI':
                return ticker

        return ""


if __name__ == '__main__':
    ProcessDB.ingestAndProcessDay('posts', 100)
    pass