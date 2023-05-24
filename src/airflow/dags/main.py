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
        start_datetime = datetime.strptime(start_datetime, "%Y-%m-%d %H:%M:%S")
        end_datetime = datetime.strptime(end_datetime, "%Y-%m-%d %H:%M:%S")
        query = {
            "query": {
                "range": {
                    "datetime": {
                        "gte": str(start_datetime.isoformat()),
                        "lt": str(end_datetime.isoformat()),
                    }
                }
            },
            "size": 10000,
        }

        scroll_url = f"{opensearch_url}/{index}/_search?scroll=1m"
        headers = {"Content-Type": "application/json"}
        response = requests.post(scroll_url, headers=headers, data=json.dumps(query))

        response_json = response.json()

        scroll_id = response_json["_scroll_id"]

        hits = response_json["hits"]["hits"]
        results = []

        while hits:
            results += [hit["_source"] for hit in hits]
            scroll_url = f"{opensearch_url}/_search/scroll"
            data = {"scroll": "1m", "scroll_id": scroll_id}
            headers = {"Content-Type": "application/json"}
            response = requests.post(scroll_url, headers=headers, data=json.dumps(data))
            response_json = response.json()
            try:
                hits = response_json["hits"]["hits"]
            except:
                break

        df = pd.DataFrame(results)
        if not os.path.exists("/opt/airflow/data"):
            os.makedirs("/opt/airflow/data")

        if df.empty:
            return False

        df.to_parquet(
            f"/opt/airflow/data/{index}_{str(start_datetime)}_{str(end_datetime)}.parquet",
            index=False,
        )
        return True

    @task(trigger_rule=TriggerRule.ALL_SUCCESS)
    def delete_exist_data(
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

    @task(trigger_rule=TriggerRule.ALL_SUCCESS)
    def insert_data_to_postgresql(
        postgres_url: str,
        table_name: str,
        index: str,
        start_datetime: str,
        end_datetime: str,
    ):
        start_datetime = datetime.strptime(start_datetime, "%Y-%m-%d %H:%M:%S")
        end_datetime = datetime.strptime(end_datetime, "%Y-%m-%d %H:%M:%S")

        engine = create_engine(postgres_url)

        df = pd.read_parquet(
            f"/opt/airflow/data/{index}_{str(start_datetime)}_{str(end_datetime)}.parquet"
        )

        df.to_sql(table_name, engine, if_exists="append", index=False)
        return "Successfully to_sql postgresql"

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
