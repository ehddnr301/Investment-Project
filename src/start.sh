#!/bin/bash

bash start_secret.sh

kubectl create configmap fluentd-config --from-file=fluentd/fluent.conf

kubectl apply -f opensearch/opensearch.yaml

kubectl apply -f ticker/ticker.yaml

kubectl apply -f opensearch_dashboard/open_dashboard.yaml

kubectl apply -f postgresql/postgresql.yaml

sleep 10;

cd minio && bash apply_minio.sh && cd ..

cd mlflow && bash create_database.sh && kubectl apply -f mlflow.yaml && cd ..

kubectl apply -f fastapi/fastapi.yaml

kubectl apply -f streamlit.yaml

cd airflow && bash edit_directory_permission.sh && bash apply_airflow.sh