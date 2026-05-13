#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="arquisoft-local"

kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/mongo/

helm upgrade --install kafka bitnami/kafka \
  --namespace "${NAMESPACE}" \
  --values k8s/kafka/values.yaml

kubectl apply -f k8s/gestor-promociones/
kubectl apply -f k8s/motor-nba-nbo/
kubectl apply -f k8s/adaptador-excel/
kubectl apply -f k8s/api-gateway/

kubectl get pods --namespace "${NAMESPACE}"
