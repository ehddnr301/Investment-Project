import os
import sys
import json

import argparse
from datetime import datetime
import multiprocessing as mp

import pyupbit
from loguru import logger


def delete_old_logs(log_dir, days_to_keep):
    NOW = datetime.now()
    for filename in os.listdir(log_dir):
        if filename.endswith(".log"):
            filepath = os.path.join(log_dir, filename)
            created_time = datetime.fromtimestamp(os.path.getctime(filepath))
            age_in_days = (NOW - created_time).days
            if age_in_days > days_to_keep:
                os.remove(filepath)


if __name__ == "__main__":
    # argparse settings
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ticker", nargs="*", default=["KRW-BTC"], help="Tickers to track"
    )
    args = parser.parse_args()

    # logging
    log_dir = "logs"
    days_to_keep = 1

    logger.remove()

    logger.add(
        os.path.join(log_dir, "logs.log"),
        format="{message}",
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
        dt = datetime.now()

        log_data = {
            "datetime": data["trade_timestamp"],
            "code": data["code"],
            "trade_price": data["trade_price"],
            "change": data["change"],
            "signed_change_price": data["signed_change_price"],
            "signed_change_rate": data["signed_change_rate"],
            "trade_volume": data["trade_volume"],
        }
        logger.info(json.dumps(log_data))


        # Check & Delete Old log files
        if dt.hour == 0 and dt.minute == 0:
            delete_old_logs(log_dir, days_to_keep)
