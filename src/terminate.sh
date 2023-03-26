#!/bin/bash

kubectl delete -f opensearch/opensearch.yaml

kubectl delete -f ticker/ticker.yaml

kubectl delete -f opensearch_dashboard/open_dashboard.yaml