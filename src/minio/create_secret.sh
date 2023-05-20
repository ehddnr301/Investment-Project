#!/bin/bash

set -e

if [ ! -f ".env" ]; then
  echo ".env file not found"
  exit 1
fi

# 환경 변수 읽어오기
export $(grep -v '^#' .env | xargs)

# Kubernetes Secret 오브젝트 생성
kubectl create secret generic minio-secret \
  --from-literal=minio-access-key=$MINIO_ACCESS_KEY \
  --from-literal=minio-secret-key=$MINIO_SECRET_KEY \
  --from-literal=minio-root-user=$MINIO_ROOT_USER \
  --from-literal=minio-root-password=$MINIO_ROOT_PASSWORD
