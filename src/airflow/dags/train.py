import os
import json
import requests

import time
import random
from datetime import datetime, timedelta

import mlflow
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

from airflow.decorators import dag, task
from airflow.utils.trigger_rule import TriggerRule

from src.ml_model_train import read_n_preprocessing_data_func, train_model


default_args = {
    "owner": "airflow",
    "start_date": datetime(2023, 5, 9),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


@dag(
    default_args=default_args,
    schedule_interval="15 * * * *",
    catchup=False,
    description="Train_Simple_Model",
    dag_id="train_simple_model",
)
def train_simple_model(
    index: str = "ticker",
    code_list: list = ["KRW-BTC", "KRW-ETH"],
    opensearch_url: str = "http://opensearch-service:9200",
    postgres_url: str = os.getenv("AIRFLOW__CORE__SQL_ALCHEMY_CONN"),
    start_datetime: str = str(datetime.now() - timedelta(hours=2))[:13] + ":00:00",
    ml_start_datetime: str = str(datetime.now() - timedelta(hours=1))[:13] + ":00:00",
    ml_end_datetime: str = str(datetime.now() - timedelta(hours=0))[:13] + ":00:00",
):
    @task()
    def read_n_preprocessing_data_task(
        code_list: list, start_datetime: str, postgres_url: str
    ):
        read_n_preprocessing_data_func(code_list, start_datetime, postgres_url)

    @task(trigger_rule=TriggerRule.ALL_SUCCESS)
    def train_model_task(
        code_list: list,
        ml_start_datetime: str,
        ml_end_datetime: str,
        opensearch_url: str,
        index: str,
    ):
        train_model(
            code_list, ml_start_datetime, ml_end_datetime, opensearch_url, index
        )

    read_data_task = read_n_preprocessing_data_task(
        code_list, start_datetime, postgres_url
    )

    train_rf_model_task = train_model_task(
        code_list, ml_start_datetime, ml_end_datetime, opensearch_url, index
    )

    read_data_task >> train_rf_model_task


train_simple_model_dag = train_simple_model()
