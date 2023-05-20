#!/bin/bash

sudo chmod 777 -R minio/

bash start_secret.sh

kubectl create configmap fluentd-config --from-file=fluentd/fluent.conf

kubectl apply -f postgresql/postgresql.yaml

sleep 10;

kubectl apply -f opensearch/opensearch.yaml

sleep 10;

kubectl apply -f ticker/ticker.yaml

sleep 10;

kubectl apply -f opensearch_dashboard/open_dashboard.yaml

sleep 180;

cd minio && bash apply_minio.sh && cd ..

sleep 10;

cd mlflow && bash create_database.sh && kubectl apply -f mlflow.yaml && cd ..

sleep 10;

kubectl apply -f fastapi/fastapi.yaml

sleep 10;

kubectl apply -f streamlit/streamlit.yaml

sleep 10;

cd airflow && bash edit_directory_permission.sh && bash apply_airflow.sh