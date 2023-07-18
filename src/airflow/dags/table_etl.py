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

from src.etl import delete_exists_data_func, create_ticker_silver_table


default_args = {
    "owner": "airflow",
    "start_date": datetime(2023, 7, 18),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


@dag(
    default_args=default_args,
    schedule_interval="30 * * * *",
    catchup=False,
    description="Table ETL",
    dag_id="medalian_etl",
)
def medalian_etl(
    postgres_url: str = os.getenv("AIRFLOW__CORE__SQL_ALCHEMY_CONN"),
    index: str = "ticker",
    from_table_name: str = "bronze_ticker",
    to_table_name: str = "silver_ticker",
    start_datetime: str = str(datetime.now() - timedelta(hours=2))[:13] + ":00:00",
    end_datetime: str = str(datetime.now() - timedelta(hours=1))[:13] + ":00:00",
):
    @task(trigger_rule=TriggerRule.ALL_SUCCESS)
    def delete_exist_data(
        postgres_url: str, to_table_name: str, start_datetime: str, end_datetime: str
    ):
        delete_exists_data_func(
            postgres_url, to_table_name, start_datetime, end_datetime
        )

    @task(trigger_rule=TriggerRule.ALL_SUCCESS)
    def insert_to_silver_table(
        postgres_url: str,
        from_table_name: str,
        to_table_name: str,
        start_datetime: str,
        end_datetime: str,
    ):
        create_ticker_silver_table(
            postgres_url, from_table_name, to_table_name, start_datetime, end_datetime
        )

    delete_db_data = delete_exist_data(
        postgres_url,
        to_table_name,
        start_datetime,
        end_datetime,
    )

    insert_to_db = insert_to_silver_table(
        postgres_url,
        from_table_name,
        to_table_name,
        start_datetime,
        end_datetime,
    )

    delete_db_data >> insert_to_db


opensearch_to_postgresql_dag = medalian_etl()
