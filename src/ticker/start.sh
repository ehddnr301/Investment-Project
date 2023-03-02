#!/bin/bash

fluentd -c /fluentd/etc/fluent.conf &

sleep 1

python3 main.py --ticker KRW-BTC KRW-ETH