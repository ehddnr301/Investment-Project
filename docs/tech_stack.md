# 사용 기술과 이유

## Intro

- 기본 모토는 돈아껴 개발해보자 입니다.
- 짠내나는 개발을 위해 Infra를 공부했습니다.

## Infra

- Terraform: GCP Compute Instance를 생성 및 삭제 하기 위해 사용하였습니다.
- Ansible: 매번 Compute Instance를 지웠다 생성하면 Docker설치, 파이썬 셋팅 등이 오래걸리기 때문에 시간을 절약하려 사용하였습니다.
    - 사용 Container가 여러개이기 때문에 오히려 K8s service를 사용하는것이 나을것 같아 Kubernetes설치를 넣어두었습니다.

## Backend

- Fastapi: 모델 서빙을 위한 백엔드 서버입니다.

## Data

- Fluentd: 로그가 떨어지는상황(본 프로젝트에서는 websocket으로 가져온 upbit정보로 이루어진 log file)을 실습하기 위해 사용한 로그수집기
- Mlflow: 모델 학습결과를 관리하기위해 사용하였습니다.
- Airflow: 데이터 배치 파이프라인, 모델학습 파이프라인 등 task scheduling 목적으로 사용하고있습니다.

## Data Store

- OpenSearch: 로그파일을 fluentd로 가져와 저장하기 위해 사용하였습니다. EFK 스택에서 E입니다.
- Postgresql: 여러 component들의 BackDB, BI 툴 연결 고려 등 다목적으로 사용하기 위함입니다.
- MinIO: 추후 S3혹은 google storage를 사용할것을 고려하여 linux file system을 Minio로 object storage처럼 사용하고 있습니다.

## Visualize

- OpenSearch DashBoard: opensearch에 저장된 데이터를 시각화 하기위해 사용하였습니다.
- Streamlit: coin 가격 정보를 시각화 하기위해 사용하였습니다. (+ 구매판매 정보)