#!/bin/bash

set -e

if [ ! -f ".env" ]; then
  echo ".env file not found"
  exit 1
fi

# 환경 변수 읽어오기
export $(grep -v '^#' .env | xargs)

# Kubernetes Secret 오브젝트 생성
kubectl create secret generic airflow-secret \
  --from-literal=airflow-core-sql-alchemy-conn=$AIRFLOW__CORE__SQL_ALCHEMY_CONN
