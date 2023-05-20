#!/bin/bash

set -e

if [ ! -f ".env" ]; then
  echo ".env file not found"
  exit 1
fi

# 환경 변수 읽어오기
export $(grep -v '^#' .env | xargs)

# Kubernetes Secret 오브젝트 생성
kubectl create secret generic mlflow-secret \
  --from-literal=mlflow-s3-endpoint-url=$MLFLOW_S3_ENDPOINT_URL \
  --from-literal=aws-access-key-id=$AWS_ACCESS_KEY_ID \
  --from-literal=aws-secret-access-key=$AWS_SECRET_ACCESS_KEY
