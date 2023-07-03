import os
import json
import time
import requests
from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import inspect

from airflow.decorators import dag, task
from airflow.utils.trigger_rule import TriggerRule

from src.opensearch_data import (
    opensearch_to_parquet,
    delete_exists_data,
    insert_parquet_to_postgresql,
)


default_args = {
    "owner": "airflow",
    "start_date": datetime(2023, 5, 7),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


@dag(
    default_args=default_args,
    schedule_interval="0 * * * *",
    catchup=False,
    description="Opensearch To postgresql",
    dag_id="opensearch_data_to_postgresql",
)
def opensearch_to_postgresql(
    opensearch_url: str = "http://opensearch-service:9200",
    postgres_url: str = os.getenv("AIRFLOW__CORE__SQL_ALCHEMY_CONN"),
    index: str = "ticker",
    table_name: str = "bronze_ticker",
    start_datetime: str = str(datetime.now() - timedelta(hours=2))[:13] + ":00:00",
    end_datetime: str = str(datetime.now() - timedelta(hours=1))[:13] + ":00:00",
):
    @task()
    def opensearch_to_parquet(
        opensearch_url: str, index: str, start_datetime: str, end_datetime: str
    ):
        opensearch_to_parquet(opensearch_url, index, start_datetime, end_datetime)

    @task(trigger_rule=TriggerRule.ALL_SUCCESS)
    def delete_exist_data(
        postgres_url: str, table_name: str, start_datetime: str, end_datetime: str
    ):
        delete_exists_data(postgres_url, table_name, start_datetime, end_datetime)

    @task(trigger_rule=TriggerRule.ALL_SUCCESS)
    def insert_data_to_postgresql(
        postgres_url: str,
        table_name: str,
        index: str,
        start_datetime: str,
        end_datetime: str,
    ):
        insert_parquet_to_postgresql(
            postgres_url, table_name, index, start_datetime, end_datetime
        )

    data_to_file = opensearch_to_parquet(
        opensearch_url, index, start_datetime, end_datetime
    )

    delete_db_data = delete_exist_data(
        postgres_url,
        table_name,
        start_datetime,
        end_datetime,
    )

    insert_to_db = insert_data_to_postgresql(
        postgres_url, table_name, index, start_datetime, end_datetime
    )

    data_to_file >> delete_db_data >> insert_to_db


opensearch_to_postgresql_dag = opensearch_to_postgresql()
