import requests
import json

# import streamlit as st
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

import matplotlib.pyplot as plt


if __name__ == "__main__":
    start_datetime = str(datetime.now() - timedelta(hours=1))
    end_datetime = str(datetime.now())
    index = "ticker"
    opensearch_url = "http://opensearch-service:9200"
    headers = {"Content-Type": "application/json"}
    start_datetime = datetime.strptime(start_datetime, "%Y-%m-%d %H:%M:%S.%f")
    end_datetime = datetime.strptime(end_datetime, "%Y-%m-%d %H:%M:%S.%f")
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

    code_list = ["KRW-BTC", "KRW-ETH"]
    for code in code_list:
        code_df = df[df["code"] == code]
        # if code == "KRW-BTC":
        #     print(code_df)

        code_df = code_df.drop_duplicates(subset=["datetime"], keep="last")
        code_df["datetime2"] = pd.to_datetime(code_df["datetime"], unit="ms")
        code_df["datetime2"] = code_df["datetime2"].dt.strftime("%Y-%m-%d %H:%M:00")
        agg_code_df = code_df.groupby("datetime2").agg(
            frequent_change=("change", lambda x: x.mode()[0]),
            average_price=("trade_price", "mean"),
            total_trade_volume=("trade_volume", "sum"),
        )
        agg_code_df["frequent_change"] = agg_code_df["frequent_change"].apply(
            lambda x: 1 if x == "RISE" else 0
        )

        agg_dict = agg_code_df.to_dict("list")

        data = {
            "model_name": "ticker_model_" + code,
            "ticker_data": agg_dict,
        }
        response = requests.post(
            "http://fastapi-service:8000/stock/next_average_price",
            headers=headers,
            data=json.dumps(data),
        )

        pred_response = pd.DataFrame.from_dict(response.json())
        pred_response.index = agg_code_df.index
        final_df = pd.concat(
            [agg_code_df, pred_response],
            axis=1,
        )
        final_df["margin"] = final_df["average_price"] - final_df["next_average_price"]

        final_df.reset_index(inplace=True)

        # Back Testing Code 넣기
        merged_df = pd.merge(code_df, pred_response, how="left", on="datetime2")
        # 초기 자본
        capital = 50000

        # 매매 기록을 저장할 리스트
        buy_transactions = []
        buy_log = []
        sell_log = []
        MAX_TRADE_TIME = 0
        for _, row in merged_df.iterrows():
            # 구매한 coin 중에 현재 가격이 구매당시 가격보다 0.2퍼센트 이상 상승한 경우 매도
            if len(buy_transactions) > 0:
                for idx, transaction in enumerate(buy_transactions):
                    if transaction["trade_price"] * 1.002 <= row["trade_price"]:
                        capital += transaction["trade_amount"] * row["trade_price"]
                        capital -= (
                            transaction["trade_amount"] * row["trade_price"] * 0.00005
                        )  # 수수료
                        sell_log.append(
                            {
                                "trade_price": row["trade_price"],  # 판매당시 가격
                                "trade_amount": transaction[
                                    "trade_amount"
                                ],  # 구매 amount
                                "trade_time": row["datetime"],
                            }
                        )

                        del buy_transactions[idx]

            # predict_price보다 현재 거래가격이 낮은경우 & trade_time이 1분이상 지난 경우 최소 거래금액으로 구매
            if len(buy_transactions) > 0:
                min_trade_time = max(buy_transactions, key=lambda x: x["trade_time"])
                MAX_TRADE_TIME = min_trade_time["trade_time"]
            if (
                row["trade_price"] < row["next_average_price"]
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
                buy_log.append(
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
            sell_log.append(
                {
                    "trade_price": row["trade_price"],  # 판매당시 가격
                    "trade_amount": transaction["trade_amount"],  # 구매 amount
                    "trade_time": row["datetime"],
                }
            )

        # Set Plot
        plt.style.use("fivethirtyeight")
        plt.rcParams["figure.figsize"] = (15, 8)

        # buy_log에서 trade_time과 trade_price 추출
        buy_trade_time = [
            str(datetime.utcfromtimestamp(item["trade_time"] / 1000))[:-9] + "00"
            for item in buy_log
        ]
        buy_trade_price = [item["trade_price"] for item in buy_log]

        # sell_log에서 trade_time과 trade_price 추출
        sell_trade_time = [
            str(datetime.utcfromtimestamp(item["trade_time"] / 1000))[:-9] + "00"
            for item in sell_log
        ]
        sell_trade_price = [item["trade_price"] for item in sell_log]

        # line_chart에 trading 기록 추가
        fig, ax = plt.subplots()
        ax.plot(final_df["datetime2"], final_df["average_price"], label="Average Price")
        ax.plot(
            final_df["datetime2"],
            final_df["next_average_price"],
            label="PredictedPrice",
        )
        ax.scatter(
            buy_trade_time,
            buy_trade_price,
            marker="^",
            color="darkblue",
            label="Buy",
            s=100,
        )
        ax.scatter(
            sell_trade_time,
            sell_trade_price,
            marker="v",
            color="crimson",
            label="Sell",
            s=100,
        )
        ax.legend()
        ax.set_title(f"{code}")
        ax.set_xlabel("Datetime")
        ax.set_ylabel("Price")
        st.pyplot(fig)
