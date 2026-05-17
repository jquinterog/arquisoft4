#!/usr/bin/env bash
set -euo pipefail

kubectl port-forward --namespace arquisoft-local service/api-gateway 8000:8000
kubectl port-forward --namespace arquisoft-local pod/motor-nba-nbo-0 8001:8000
