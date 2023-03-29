#!/bin/bash

kubectl create configmap fluentd-config --from-file=fluentd/fluent.conf

kubectl apply -f opensearch/opensearch.yaml

kubectl apply -f ticker/ticker.yaml

kubectl apply -f opensearch_dashboard/open_dashboard.yaml

kubectl apply -f postgresql/postgresql.yaml