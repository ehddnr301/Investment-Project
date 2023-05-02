import os
import json
import time
import requests
from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import create_engine
from airflow.decorators import dag, task
from airflow.utils.dates import days_ago

default_args = {
    "owner": "airflow",
    "start_date": datetime(2023, 4, 25),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


@dag(
    default_args=default_args,
    schedule_interval="0 1 * * *",
    catchup=False,
    description="Opensearch To postgresql",
    dag_id="opensearch_to_postgresql",
)
def opensearch_to_postgresql():
    @task()
    def search_ticker_data() -> pd.DataFrame:
        host = "http://opensearch-service:9200"
        index = "ticker"
        start_date = (datetime.now() - timedelta(days=1)).date()
        end_date = datetime.now().date()
        # unix_time_start_date = time.mktime(start_date.timetuple()) * 1000
        # unix_time_end_date = time.mktime(end_date.timetuple()) * 1000

        query = {
            "query": {
                "range": {
                    "datetime": {
                        "gte": str(start_date.isoformat()),
                        "lt": str(end_date.isoformat()),
                    }
                }
            },
            "size": 10000,
        }

        scroll_url = f"{host}/{index}/_search?scroll=1m"
        headers = {"Content-Type": "application/json"}
        response = requests.post(scroll_url, headers=headers, data=json.dumps(query))

        response_json = response.json()

        scroll_id = response_json["_scroll_id"]

        hits = response_json["hits"]["hits"]
        results = []

        while hits:
            results += [hit["_source"] for hit in hits]
            scroll_url = f"{host}/_search/scroll"
            data = {"scroll": "1m", "scroll_id": scroll_id}
            headers = {"Content-Type": "application/json"}
            response = requests.post(scroll_url, headers=headers, data=json.dumps(data))
            response_json = response.json()
            try:
                hits = response_json["hits"]["hits"]
            except:
                break

        try:
            df = pd.DataFrame(results)
            if not os.path.exists("/opt/airflow/data"):
                os.makedirs("/opt/airflow/data")
            df.to_parquet("/opt/airflow/data/ticker.parquet", index=False)
            return True
        except Exception as e:
            print(e)
            return False

    @task()
    def insert_data_to_postgresql(
        is_success: bool,
    ):
        if not is_success:
            return
        engine = create_engine(
            "postgresql+psycopg2://postgres:postgres@postgres-service/postgres"
        )
        df = pd.read_parquet(f"/opt/airflow/data/ticker.parquet")
        df.to_sql("ticker", engine, if_exists="append", index=False)
        return "Done"

    is_success = search_ticker_data()

    insert_data_to_postgresql(is_success)


opensearch_to_postgresql_dag = opensearch_to_postgresql()