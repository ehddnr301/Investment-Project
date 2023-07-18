import os
import time
from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import inspect

from src.supports.opensearch import OpenSearchRequest


def opensearch_to_parquet_func(
    opensearch_url: str, index: str, start_datetime: str, end_datetime: str
):
    osr = OpenSearchRequest(opensearch_url, index)
    osr.set_datetime_range_query(start_datetime, end_datetime, 10000)

    df = osr.get_query_result_scroll_api()

    if not os.path.exists("/opt/airflow/data"):
        os.makedirs("/opt/airflow/data")

    if df.empty:
        return False

    df.to_parquet(
        f"/opt/airflow/data/{index}_{str(start_datetime)}_{str(end_datetime)}.parquet",
        index=False,
    )

    return True

def insert_parquet_to_postgresql(
    postgres_url: str,
    table_name: str,
    index: str,
    start_datetime: str,
    end_datetime: str,
):
    engine = create_engine(postgres_url)

    df = pd.read_parquet(
        f"/opt/airflow/data/{index}_{str(start_datetime)}_{str(end_datetime)}.parquet"
    )

    df.to_sql(table_name, engine, if_exists="append", index=False)
    return "Successfully to_sql postgresql"
