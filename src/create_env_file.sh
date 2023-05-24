echo "DB_NAME=postgres" >> postgresql/.env
echo "DB_USER=postgres" >> postgresql/.env
echo "DB_PASSWORD=postgres" >> postgresql/.env

echo "OPENSEARCH_HOSTS=http://opensearch-service:9200" >> opensearch_dashboard/.env
echo "DISABLE_SECURITY_DASHBOARDS_PLUGIN=true" >> opensearch_dashboard/.env

echo "MLFLOW_S3_ENDPOINT_URL=http://minio-service:9000/" >> mlflow/.env
echo "AWS_ACCESS_KEY_ID=test_user_id" >> mlflow/.env
echo "AWS_SECRET_ACCESS_KEY=test_user_password" >> mlflow/.env

echo "MINIO_ACCESS_KEY=test_access_key" >> minio/.env
echo "MINIO_SECRET_KEY=test_secret_key" >> minio/.env
echo "MINIO_ROOT_USER=test_user_id" >> minio/.env
echo "MINIO_ROOT_PASSWORD=test_user_password" >> minio/.env

echo "AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://postgres:postgres@postgres-service:5432/postgres" >> airflow/.env