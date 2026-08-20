"""Transform raw Reddit posts and persist analyzed results."""

import re

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import bindparam, text as sql_text
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from db.connection import get_engine
from src.pipeline.ingest import RawDataIngestor
from src.pipeline.sentiment import SentimentPipeline
from src.pipeline.tickers import extract_tickers


def _insert_ignoring_duplicate_titles(table, connection, keys, data_iter):
    rows = [dict(zip(keys, row)) for row in data_iter]
    if not rows:
        return 0
    insert_factory = (
        sqlite_insert if connection.dialect.name == "sqlite" else postgres_insert
    )
    statement = insert_factory(table.table).values(rows).on_conflict_do_nothing(
        index_elements=["text"]
    )
    return connection.execute(statement).rowcount


class ProcessDB:
    @staticmethod
    def _engine():
        load_dotenv()
        return get_engine()

    @staticmethod
    def _ingest(period: str, table: str) -> pd.DataFrame:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table):
            raise ValueError("Invalid database table name")

        engine = ProcessDB._engine()
        ingest = RawDataIngestor()
        raw_df = ingest.get_last_day() if period == "day" else ingest.get_last_week()
        if raw_df.empty:
            return raw_df

        raw_df = raw_df.drop_duplicates(subset=["text"])
        titles = raw_df["text"].dropna().astype(str).tolist()
        if titles:
            query = sql_text(f"SELECT text FROM {table} WHERE text IN :titles").bindparams(
                bindparam("titles", expanding=True)
            )
            with engine.connect() as connection:
                existing_titles = set(connection.execute(query, {"titles": titles}).scalars())
            raw_df = raw_df[~raw_df["text"].isin(existing_titles)]
        if raw_df.empty:
            return raw_df

        model = SentimentPipeline()
        processed_df = ProcessDB.processR(raw_df, model)
        if processed_df.empty:
            return processed_df

        processed_df.to_sql(
            table,
            engine,
            if_exists="append",
            index=False,
            chunksize=100,
            method=_insert_ignoring_duplicate_titles,
        )
        return processed_df

    @staticmethod
    def ingestAndProcessDay(db: str) -> pd.DataFrame:
        return ProcessDB._ingest("day", db)

    @staticmethod
    def ingestAndProcessWeek(db: str) -> pd.DataFrame:
        return ProcessDB._ingest("week", db)

    @staticmethod
    def processR(df: pd.DataFrame, model) -> pd.DataFrame:
        """Add normalized ticker symbols and financial sentiment scores."""

        if df.empty:
            return df.copy()

        processed = df.copy()
        titles = processed["text"].fillna("").astype(str)
        bodies = processed["post_text"].fillna("").astype(str)
        combined_text = (titles + " " + bodies).str.strip()

        if hasattr(model, "analyze_batch"):
            scores = model.analyze_batch(combined_text.tolist())
        else:
            scores = [model.analyze(text)[0] for text in combined_text]

        processed[["positive", "negative", "neutral"]] = scores
        processed["confidence"] = processed[
            ["positive", "negative", "neutral"]
        ].max(axis=1)
        processed["tickers"] = combined_text.map(ProcessDB.getTickers)
        return processed

    getTickers = staticmethod(extract_tickers)


if __name__ == "__main__":
    ProcessDB.ingestAndProcessWeek("posts")
