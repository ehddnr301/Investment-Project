import requests
import json

# import streamlit as st
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

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

        st.line_chart(
            final_df, x="datetime2", y=["average_price", "next_average_price"]
        )
