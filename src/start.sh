#!/bin/bash

bash start_secret.sh

kubectl create configmap fluentd-config --from-file=fluentd/fluent.conf

kubectl apply -f postgresql/postgresql.yaml

sleep 60;

kubectl apply -f opensearch/opensearch.yaml

sleep 60;

kubectl apply -f ticker/ticker.yaml

sleep 60;

kubectl apply -f opensearch_dashboard/open_dashboard.yaml

sleep 60;

cd minio && bash apply_minio.sh && cd ..

sleep 60;

cd mlflow && bash create_database.sh && kubectl apply -f mlflow.yaml && cd ..

sleep 60;

kubectl apply -f fastapi/fastapi.yaml

sleep 60;

kubectl apply -f streamlit/streamlit.yaml

sleep 60;

cd airflow && bash edit_directory_permission.sh && bash apply_airflow.sh