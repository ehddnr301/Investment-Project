#!/bin/bash

sed -i  "s/\${USER}/$(echo $USER | awk '{print $1}')/g" minio.yaml
sed -i "s/\${SERVER_IP}/$(ifconfig ens4 | grep 'inet ' | awk '{print $2}')/g" minio.yaml

kubectl apply -f minio.yaml