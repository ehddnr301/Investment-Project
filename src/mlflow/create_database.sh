#!/bin/bash

export MY_POSTGRESQL=$(kubectl get pods | grep postgres | awk '{print $1}')

kubectl exec -it $MY_POSTGRESQL \
-- psql -U postgres \
-c "CREATE DATABASE mlflow"