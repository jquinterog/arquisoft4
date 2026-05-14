#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="arquisoft-local"

kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/mongo/
kubectl apply -f k8s/kafka.yaml
kubectl rollout status deployment/kafka --namespace "${NAMESPACE}" --timeout=180s

kubectl apply -f k8s/gestor-promociones/
kubectl apply -f k8s/motor-nba-nbo/
kubectl apply -f k8s/adaptador-excel/
kubectl apply -f k8s/api-gateway/

kubectl get pods --namespace "${NAMESPACE}"
