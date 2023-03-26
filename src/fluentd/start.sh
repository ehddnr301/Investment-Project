#!/bin/bash

until nc -z opensearch-service 9200; do
  sleep 5
done

curl -XPUT opensearch-service:9200/ticker

curl -XPUT opensearch-service:9200/ticker/_mapping \
	-H "Content-Type: application/json" \
	-d '
{
  "properties": {
    "datetime": {
      "type": "date"
    },
    "code": {
      "type": "keyword"
    },
    "trade_price": {
      "type": "integer"
    },
    "change": {
      "type": "keyword"
    },
    "signed_change_price": {
      "type": "float"
    },
    "signed_change_rate": {
      "type": "float"
    },
    "trade_volume": {
      "type": "float"
    }
  }
}
'

fluentd -c /fluentd/etc/fluent.conf