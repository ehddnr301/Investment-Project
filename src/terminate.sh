#!/bin/bash

kubectl delete -f opensearch/opensearch.yaml

kubectl delete -f ticker/ticker.yaml

kubectl delete -f opensearch_dashboard/open_dashboard.yaml

kubectl delete -f postgresql/postgresql.yaml

kubectl delete -f fastapi/fastapi.yaml

kubectl delete -f mlflow/mlflow.yaml

kubectl delete -f minio/minio.yaml

kubectl delete -f streamlit/streamlit.yaml

kubectl delete -f airflow/airflow.yaml
