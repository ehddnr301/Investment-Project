import os
import json
import requests

import time
import random
from datetime import datetime, timedelta

import mlflow
import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

from src.supports.opensearch import OpenSearchRequest
from src.supports.mlflow import (
    create_new_mlflow_model,
    create_model_version,
    update_registered_model,
)


def read_n_preprocessing_data_func(
    code_list: list, start_datetime: str, postgres_url: str
):
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


def train_model(
    code_list: list,
    start_datetime: str,
    end_datetime: str,
    opensearch_url: str,
    index: str,
):
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
            param: random.choice(param_ranges[param]) for param in param_ranges.keys()
        }

        # Model Train
        model = RandomForestRegressor(random_state=42, **params)

        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)

        # Test Set 으로 Back Testing 결과 내보기

        START_MONEY = 50000
        osr = OpenSearchRequest(opensearch_url, index)
        osr.set_datetime_range_query(start_datetime, end_datetime, 10000)

        opensearch_df = osr.get_query_result_scroll_api()

        code_df = opensearch_df[opensearch_df["code"] == code]
        code_df["datetime2"] = pd.to_datetime(code_df["datetime"], unit="ms")
        preprocessed_df = code_df.drop_duplicates(subset=["datetime"], keep="last")
        preprocessed_df["datetime2"] = preprocessed_df["datetime2"].dt.strftime(
            "%Y-%m-%d %H:%M:00"
        )

        agg_df = preprocessed_df.groupby("datetime2").agg(
            frequent_change=("change", lambda x: x.mode()[0]),
            average_price=("trade_price", "mean"),
            total_trade_volume=("trade_volume", "sum"),
        )
        agg_df["frequent_change"] = agg_df["frequent_change"].apply(
            lambda x: 1 if x == "RISE" else 0
        )

        result = model.predict(agg_df)

        agg_df["predict_result"] = result
        agg_df["predict_result"] = agg_df["predict_result"].shift(1)
        agg_df = agg_df.reset_index()[["datetime2", "predict_result"]]
        code_df["datetime2"] = code_df["datetime2"].map(lambda x: str(x)[:16] + ":00")

        merged_df = pd.merge(code_df, agg_df, how="left", on="datetime2")

        # 초기 자본
        capital = START_MONEY

        # 매매 기록을 저장할 리스트
        buy_transactions = []
        MAX_TRADE_TIME = 0

        # 백테스팅 전략
        for _, row in merged_df.iterrows():
            # 구매한 coin 중에 현재 가격이 구매당시 가격보다 0.2퍼센트 이상 상승한 경우 매도
            if len(buy_transactions) > 0:
                for idx, transaction in enumerate(buy_transactions):
                    if transaction["trade_price"] * 1.002 <= row["trade_price"]:
                        capital += transaction["trade_amount"] * row["trade_price"]
                        capital -= (
                            transaction["trade_amount"] * row["trade_price"] * 0.00005
                        )
                        del buy_transactions[idx]

            # predict_price보다 현재 거래가격이 낮은경우 & trade_time이 1분이상 지난 경우 최소 거래금액으로 구매
            if len(buy_transactions) > 0:
                min_trade_time = max(buy_transactions, key=lambda x: x["trade_time"])
                MAX_TRADE_TIME = min_trade_time["trade_time"]
            if (
                row["trade_price"] < row["predict_result"]
                and capital > 5000.25
                and MAX_TRADE_TIME + (1000 * 60 * 1) < row["datetime"]
            ):
                # 현재 가격이 예측 가격보다 낮은 경우 주식을 구매
                buy_transactions.append(
                    {
                        "trade_price": row["trade_price"],  # 구매당시 가격
                        "trade_amount": 5000 / row["trade_price"],  # 구매 amount
                        "trade_time": row["datetime"],
                    }
                )
                capital -= 5000.25

        # 마지막 가격으로 전부 매도
        for transaction in buy_transactions:
            capital += (
                transaction["trade_amount"] * merged_df.iloc[-1, :]["trade_price"]
            )

        # MAE 계산
        mae = mean_absolute_error(y_test[1:], y_pred[:-1])
        metrics = {
            "MAE": mae,
            "InitialCapital": START_MONEY,
            "EndCapital": capital,
            "Profit": capital - START_MONEY,
        }
        mlflow.set_tracking_uri("http://mlflow-service:5000")
        mlflow.set_experiment(f"ticker_{code}")
        MODEL_NAME = f"ticker_model_{code}"
        with mlflow.start_run():
            mlflow.log_params(params)
            mlflow.log_metrics(metrics)
            current_model = mlflow.sklearn.log_model(model, MODEL_NAME)

            run_id, model_uri = current_model.run_id, current_model.model_uri

            create_new_mlflow_model(MODEL_NAME)
            model_version = create_model_version(MODEL_NAME, run_id, model_uri)
            update_registered_model(MODEL_NAME, model_version, "Profit", "maximize")
