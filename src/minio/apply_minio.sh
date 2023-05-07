#!/bin/bash

sed -i "s/\${SERVER_IP}/$(ifconfig ens4 | grep 'inet ' | awk '{print $2}')/g" minio.yaml

kubectl apply -f minio.yaml