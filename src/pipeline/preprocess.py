import os
import re

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

from src.pipeline.CompanyTickers import COMPANY_TICKERS
from src.pipeline.ingest import RawDataIngestor
from src.pipeline.sentiment import SentimentPipeline


class ProcessDB():

    @staticmethod
    def ingestAndProcessDay(db):
        '''
        Runs the full data pipeline to get the last day's data and add the processed version to the pipeline
        '''
        load_dotenv('/Users/fastcheetah/PycharmProjects/MarketSent/.env')
        db_connection_str = os.getenv("DB_CONNECTION_STRING")
        engine = create_engine(db_connection_str)

        ingest = RawDataIngestor()
        model = SentimentPipeline()
        raw_df = ingest.get_last_day()
        processed_df = ProcessDB.processR(raw_df, model)

        processed_df.to_sql(db, engine, if_exists='append', index=False)

        return processed_df

    @staticmethod
    def ingestAndProcessWeek(db):
        '''
        Runs the full data pipeline to get the last week's data and add the processed version to the pipeline
        '''
        load_dotenv('/Users/fastcheetah/PycharmProjects/MarketSent/.env')
        db_connection_str = os.getenv("DB_CONNECTION_STRING")
        engine = create_engine(db_connection_str)

        ingest = RawDataIngestor()
        model = SentimentPipeline()
        raw_df = ingest.get_last_week()

        processed_df = ProcessDB.processR(raw_df, model)

        for _, row in processed_df.iterrows():
            try:
                row.to_frame().T.to_sql(db, engine, if_exists='append', index=False)
            except Exception as e:
                print(f"Error inserting row: {e}")
                pass


        return processed_df


    @staticmethod
    def processR(df, model):
        '''
        Processes the raw reddit data by adding the ticker and sentiment score
        '''
        # Add sentiment scores
        df[['positive', 'negative', 'neutral']] = df.apply(
            lambda row: pd.Series(model.analyze(row['text'] + ' ' + row['post_text'])[0]),
            axis=1
        )

        df['tickers'] = df.apply(
            lambda row: ProcessDB.getTickers(row['text'] + ' ' + row['post_text']),
            axis=1
        )

        return df


    @staticmethod
    def getTickers(title):
        # Remove YOLO (not a ticker lol)
        title = title.replace('YOLO', '')
        ticker_list = []

        ticker_pattern = r'\b([A-Z]{2,5}(?:\.[A-Z]{1,3})?)\b'
        matches = re.findall(ticker_pattern, title)

        word_list = title.split()
        word_list = [item.lower() for item in word_list]
        for word in word_list:
            if word in COMPANY_TICKERS:
                if not (COMPANY_TICKERS[word] in ticker_list):
                    ticker_list.append(COMPANY_TICKERS[word])

        # Return first match that isn't AI
        #for ticker in matches:
        #    if ticker != 'AI' and ticker != 'US' and ticker != 'CEO' and ticker != 'LOL' and ticker != 'LOVE' and ticker != 'BULL':
        #        ticker_list.append(ticker)

        if len(ticker_list) > 0:
            return ticker_list


        return None


if __name__ == '__main__':
    ProcessDB.ingestAndProcessWeek('posts')