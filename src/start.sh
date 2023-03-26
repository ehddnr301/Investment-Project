#!/bin/bash

kubectl apply -f opensearch/opensearch.yaml

kubectl apply -f ticker/ticker.yaml

kubectl apply -f opensearch_dashboard/open_dashboard.yaml