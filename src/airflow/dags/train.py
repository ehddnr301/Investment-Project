import os

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
    start_date_time: str = str(datetime.now() - timedelta(hours=2))[:13] + ":00:00",
):
    @task()
    def read_n_preprocessing_data_task(code_list: list, start_datetime: str):
        postgres_url = os.getenv("AIRFLOW__CORE__SQL_ALCHEMY_CONN")
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
            df = df.drop_duplicates(subset=["datetime"], keep="last")
            df["datetime2"] = pd.to_datetime(df["datetime"], unit="ms")
            df["datetime2"] = df["datetime2"].dt.strftime("%Y-%m-%d %H:%M:00")
            # 시간별로 Aggregation된 Feature 생성
            agg_df = df.groupby("datetime2").agg(
                frequent_change=("change", lambda x: x.mode()[0]),
                average_price=("trade_price", "mean"),
                total_trade_volume=("trade_volume", "sum"),
            )
            agg_df["frequent_change"] = agg_df["frequent_change"].apply(
                lambda x: 1 if x == "RISE" else 0
            )
            agg_df["next_average_price"] = agg_df["average_price"].shift(-1)
            agg_df.dropna(inplace=True)
            if not os.path.exists("/opt/airflow/data"):
                os.makedirs("/opt/airflow/data")
            agg_df.to_parquet(f"/opt/airflow/data/{code}")
        return "Done"

    @task(trigger_rule=TriggerRule.ALL_SUCCESS)
    def train_model_task(code_list: list, start_date_time: str):
        # Read Data & drop duplicate time Preprocessing
        for code in code_list:
            df = pd.read_parquet(f"/opt/airflow/data/{code}")

            # train, test set으로 나누기
            train_data = df.iloc[:-10]
            valid_data = df.iloc[-10:]

            # Split X, Y
            X_train = train_data.drop("next_average_price", axis=1)
            y_train = train_data["next_average_price"]
            X_test = valid_data.drop("next_average_price", axis=1)
            y_test = valid_data["next_average_price"]

            param_ranges = {
                "n_estimators": range(50, 101),
                "max_depth": range(5, 16),
                "min_samples_split": range(2, 6),
                "min_samples_leaf": range(1, 6),
                "max_features": ["auto", "sqrt"],
            }

            # 랜덤으로 파라미터 선택
            params = {
                param: random.choice(param_ranges[param])
                for param in param_ranges.keys()
            }

            # Model Train
            model = RandomForestRegressor(random_state=42, **params)

            model.fit(X_train, y_train)

            y_pred = model.predict(X_test)

            # MAE 계산
            mae = mean_absolute_error(y_test, y_pred)

            mlflow.set_tracking_uri("http://mlflow-service:5000")
            mlflow.set_experiment(f"ticker_{code}")
            with mlflow.start_run():
                mlflow.log_params(params)
                mlflow.log_metric("MAE", mae)
                mlflow.sklearn.log_model(model, f"ticker_model_{code}")

    read_data_task = read_n_preprocessing_data_task(code_list, start_date_time)

    train_rf_model_task = train_model_task(code_list, start_date_time)

    read_data_task >> train_rf_model_task


train_simple_model_dag = train_simple_model()
