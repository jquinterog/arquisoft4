#!/usr/bin/env bash
set -euo pipefail

kubectl port-forward --namespace arquisoft-local service/api-gateway 8000:8000
