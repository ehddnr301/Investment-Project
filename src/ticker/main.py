import argparse
import datetime
import multiprocessing as mp
import os

import pyupbit
from loguru import logger


def delete_old_logs(log_dir, days_to_keep):
    NOW = datetime.datetime.now()
    for filename in os.listdir(log_dir):
        if filename.endswith(".log"):
            filepath = os.path.join(log_dir, filename)
            created_time = datetime.datetime.fromtimestamp(os.path.getctime(filepath))
            age_in_days = (NOW - created_time).days
            if age_in_days > days_to_keep:
                os.remove(filepath)


if __name__ == "__main__":

    # argparse 설정
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ticker", nargs="*", default=["KRW-BTC"], help="Tickers to track"
    )
    args = parser.parse_args()

    # logging
    log_dir = "logs"
    days_to_keep = 1

    logger.add(
        os.path.join(log_dir, "logs.log"),
        format="{time:YYYY-MM-DD HH:mm:ss} {message}",
        serialize=True,
        rotation="1 days",
    )

    queue = mp.Queue()
    proc = mp.Process(
        target=pyupbit.WebSocketClient,
        args=("ticker", args.ticker, queue),
        daemon=True,
    )
    proc.start()

    while True:
        data = queue.get()
        code = data["code"]
        ts = data["trade_timestamp"]
        trade_price = data["trade_price"]
        change = data["change"]
        signed_change_price = data["signed_change_price"]
        signed_change_rate = data["signed_change_rate"]
        trade_volume = data["trade_volume"]

        dt = datetime.datetime.fromtimestamp(ts / 1000)
        logger.info(
            {
                "datetime": str(dt),
                "code": code,
                "trade_price": trade_price,
                "change": change,
                "signed_change_price": signed_change_price,
                "signed_change_rate": signed_change_rate,
                "trade_volume": trade_volume,
            }
        )

        # Check & Delete Old log files
        if dt.hour == 0 and dt.minute == 0:
            delete_old_logs(log_dir, days_to_keep)
