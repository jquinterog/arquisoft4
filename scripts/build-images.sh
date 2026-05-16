#!/usr/bin/env bash
set -euo pipefail

docker build -t arquisoft/api-gateway:local ./api-gateway
docker build -t arquisoft/motor-nba-nbo:local ./motor-nba-nbo
docker build -t arquisoft/componente-promociones:local ./componente-promociones
docker build -t arquisoft/adaptador-excel:local ./adaptador-excel
