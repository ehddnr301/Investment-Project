#!/bin/bash

kubectl create configmap fluentd-config --from-file=fluentd/fluent.conf

kubectl apply -f opensearch/opensearch.yaml

kubectl apply -f ticker/ticker.yaml

kubectl apply -f opensearch_dashboard/open_dashboard.yaml

cd postgresql && bash create_secret.sh && cd ..

kubectl apply -f postgresql/postgresql.yaml

cd airflow && bash edit_directory_permission.sh && bash apply_airflow.sh