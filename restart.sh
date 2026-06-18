#!/bin/bash
# 重启服务
cd "$(dirname "$0")"
docker compose down
docker compose up -d
docker compose logs -f --tail 20
