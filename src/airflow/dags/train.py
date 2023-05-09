import os

import time
from datetime import datetime, timedelta

import mlflow
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

from airflow.decorators import dag, task
from airflow.utils.trigger_rule import TriggerRule


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
    code_list: list = ["KRW-BTC", "KRW-ETH"],
    start_date_time: str = str(datetime.now() - timedelta(hours=48))[:13] + ":00:00",
):
    @task()
    def read_train_data_task(code_list: list, start_datetime: str):
        postgres_url = (
            "postgresql+psycopg2://postgres:postgres@postgres-service/postgres"
        )
        start_datetime = str(datetime.now() - timedelta(hours=48))[:13] + ":00:00"
        start_datetime = datetime.strptime(start_datetime, "%Y-%m-%d %H:%M:%S")
        start_unix_datetime = time.mktime(start_datetime.timetuple()) * 1000

        engine = create_engine(postgres_url)
        sql = """
            SELECT * 
            FROM bronze_ticker 
            WHERE datetime >= {}
            AND code = '{}'
            ORDER BY datetime
        """

        for code in code_list:
            query = sql.format(start_unix_datetime, code)
            df = pd.read_sql(query, con=engine)
            if not os.path.exists("/opt/airflow/data"):
                os.makedirs("/opt/airflow/data")
            df.to_parquet(f"/opt/airflow/data/{code}")

        return "Done"

    @task(trigger_rule=TriggerRule.ALL_SUCCESS)
    def train_model_task(code_list: list):
        # Read Data & drop duplicate time Preprocessing
        for code in code_list:
            df = pd.read_parquet(f"/opt/airflow/data/{code}")
            df = df.drop_duplicates(subset=["datetime"], keep="last")
            df["datetime2"] = pd.to_datetime(df["datetime"], unit="ms")
            df["datetime2"] = df["datetime2"].dt.strftime("%Y-%m-%d %H:00:00")
            # 시간별로 Aggregation된 Feature 생성
            df2 = df.groupby("datetime2").agg(
                frequent_change=("change", lambda x: x.mode()[0]),
                average_price=("trade_price", "mean"),
                total_trade_volume=("trade_volume", "sum"),
            )

            df2["frequent_change"] = df2["frequent_change"].apply(
                lambda x: 1 if x == "RISE" else 0
            )
            # train, test set으로 나누기
            train_data = df2.iloc[:-1]
            valid_data = df2.iloc[-1:]

            # Split X, Y
            X_train = train_data.drop("average_price", axis=1)
            y_train = train_data["average_price"]
            X_test = valid_data.drop("average_price", axis=1)
            y_test = valid_data["average_price"]

            params = {"n_estimators": 100, "random_state": 42}

            # Model Train
            model = RandomForestRegressor(**params)

            model.fit(X_train, y_train)

            y_pred = model.predict(X_test)

            # MAE 계산
            mae = mean_absolute_error(y_test, y_pred)

            os.environ["AWS_ACCESS_KEY_ID"] = "test_user_id"
            os.environ["AWS_SECRET_ACCESS_KEY"] = "test_user_password"
            os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://minio-service:9000"
            mlflow.set_tracking_uri("http://mlflow-service:5000")
            mlflow.set_experiment(f"ticker_{code}")
            with mlflow.start_run():
                mlflow.log_params(params)
                mlflow.log_metric("MAE", mae)
                mlflow.sklearn.log_model(model, f"ticker_model_{code}")

    read_data_task = read_train_data_task(code_list, start_date_time)

    train_rf_model_task = train_model_task(code_list)

    read_data_task >> train_rf_model_task


train_simple_model_dag = train_simple_model()
