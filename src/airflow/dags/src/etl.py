import time
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy import inspect
from sqlalchemy.engine.base import Engine

import pandas as pd


def delete_exists_data_func(
    postgres_url: str, table_name: str, start_datetime: str, end_datetime: str
):
    start_datetime = datetime.strptime(start_datetime, "%Y-%m-%d %H:%M:%S")
    end_datetime = datetime.strptime(end_datetime, "%Y-%m-%d %H:%M:%S")
    start_unix_datetime = time.mktime(start_datetime.timetuple()) * 1000
    end_unix_datetime = time.mktime(end_datetime.timetuple()) * 1000

    engine = create_engine(postgres_url)
    inspector = inspect(engine)

    is_table_exists = inspector.has_table(table_name)

    if not is_table_exists:
        return

    delete_query = f"""
        DELETE FROM {table_name}
        WHERE datetime >= {start_unix_datetime}
        AND datetime <= {end_unix_datetime}
    """

    with engine.begin() as conn:
        conn.execute(delete_query)


def preprocess_ticker_silver_table(
    engine: Engine,
    from_table_name: str,
    start_unix_datetime: str,
    end_unix_datetime: str,
):
    query = f"""
        SELECT * 
        FROM {from_table_name} 
        WHERE datetime >= {start_unix_datetime}
        AND datetime < {end_unix_datetime}
        ORDER BY datetime
    """
    with engine.begin() as conn:
        df = pd.read_sql(query, con=conn)

        df["datetime"] = df["datetime"].map(lambda x: x // 1000 * 1000)
        df = (
            df.groupby(["code", "datetime"])
            .agg(
                {
                    "trade_price": "max",
                    "signed_change_price": "max",
                    "signed_change_rate": "max",
                    "trade_volume": "sum",
                }
            )
            .reset_index()
        )
        return df


def create_ticker_silver_table(
    postgres_url: str,
    from_table_name: str,
    to_table_name: str,
    start_datetime: str,
    end_datetime: str,
):
    start_datetime = datetime.strptime(start_datetime, "%Y-%m-%d %H:%M:%S")
    end_datetime = datetime.strptime(end_datetime, "%Y-%m-%d %H:%M:%S")
    start_unix_datetime = time.mktime(start_datetime.timetuple()) * 1000
    end_unix_datetime = time.mktime(end_datetime.timetuple()) * 1000

    engine = create_engine(postgres_url)
    inspector = inspect(engine)

    is_from_table_exists = inspector.has_table(from_table_name)

    if not is_from_table_exists:
        return

    df = preprocess_ticker_silver_table(
        engine, from_table_name, start_unix_datetime, end_unix_datetime
    )

    df.to_sql(to_table_name, engine, if_exists="append", index=False)
