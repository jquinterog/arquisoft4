#!/usr/bin/env bash
set -euo pipefail

docker build -t arquisoft/api-gateway:local ./api-gateway
docker build -t arquisoft/motor-nba-nbo:local ./motor-nba-nbo
docker build -t arquisoft/gestor-promociones:local ./gestor-promociones
docker build -t arquisoft/adaptador-excel:local ./adaptador-excel
