#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-arquisoft-local}"
DB_USER="${DB_USER:-postgres}"
DB_NAME="${DB_NAME:-teknoshop_campaigns}"

DEFAULT_SQL="select created_at, name, channel from campaigns order by created_at desc limit 20;"
SQL="${*:-$DEFAULT_SQL}"

kubectl exec -i --namespace "${NAMESPACE}" deploy/postgres -- \
  psql \
    --username "${DB_USER}" \
    --dbname "${DB_NAME}" \
    --set "pager=off" \
    --command "${SQL}"
